"""Authenticated orchestration of private assessment and publication owners."""

import json

from amphora_contracts_research import (
    AssessmentPublicationStatus,
    EvidenceAssessmentProfile,
    EvidenceAssessmentStatus,
)
from amphora_tool_protocol import HttpTransport

from ..assessment.boundary import ConfiguredAssessment
from ..assessment.policy import AssessmentError, _identifier
from ..assessment.reader import AssessmentDataReader
from ..assessment.resolution import AssessmentResolver
from ..assessment.store import AssessmentStore
from ..persistence.ledger import IdentityLedger
from ..publication.store import PublicationStore
from ..publication.workflow import PublicationWorkflow


class AssessmentOperations:
    def __init__(self, engine, profiles, endpoint, read_token, publisher, issuer, publication_token):
        if not isinstance(profiles, list) or not 1 <= len(profiles) <= 32:
            raise ValueError("invalid_assessment_profiles")
        self.profiles = {}
        versions = set()
        for raw in profiles:
            configured = ConfiguredAssessment.from_wire(EvidenceAssessmentProfile.model_validate_json(json.dumps(raw)))
            key = configured.reference
            version = (key.scope, key.profile_id, key.version)
            if version in versions:
                raise ValueError("duplicate_assessment_profile")
            versions.add(version)
            self.profiles[key] = configured
        _identifier(publisher)
        _identifier(issuer)
        self.engine, self.endpoint, self.read_token = engine, endpoint, read_token
        self.publisher, self.issuer, self.publication_token = publisher, issuer, publication_token
        # Validate endpoints/credentials without any peer I/O or retained token logging.
        for profile in self.profiles:
            self.reader(profile.scope)
        HttpTransport(endpoint, publication_token)

    def reader(self, scope):
        return AssessmentDataReader(self.endpoint, self.read_token, scope)

    @staticmethod
    def _status(stored):
        outcome = ({"status": "pending"} if stored.resolved is None else
                   {"status": "assessed", "assessment": stored.resolved.assessment.model_dump(mode="json")})
        return EvidenceAssessmentStatus.model_validate_json(json.dumps({"wire_version": "1",
            "request": stored.intent.bound.request.model_dump(mode="json"), "actor_id": stored.intent.bound.actor_id,
            "outcome": outcome}))

    def read(self, principal, request):
        principal.require("read_assessment", request.profile.scope)
        stored = AssessmentStore(self.engine).read(request.profile.scope, request.assessment_id, principal.actor_id)
        if stored is None:
            return None
        if stored.intent.bound.request != request:
            raise AssessmentError("assessment_identity_conflict")
        return self._status(stored)

    def submit(self, principal, request):
        principal.require("assess", request.profile.scope)
        store = AssessmentStore(self.engine)
        existing = store.read(request.profile.scope, request.assessment_id, principal.actor_id)
        if existing is not None:
            if existing.intent.bound.request != request:
                raise AssessmentError("assessment_identity_conflict")
            if existing.resolved is not None:
                return self._status(existing)
        configured = self.profiles.get(request.profile)
        if configured is None:
            raise AssessmentError("assessment_profile_unavailable")
        bound = configured.bind(request, principal.actor_id, principal.scope)
        store.begin(bound)
        resolved = AssessmentResolver(IdentityLedger(self.engine), self.reader(principal.scope)).resolve(bound)
        return self._status(store.complete(bound, resolved))

    @staticmethod
    def _publication_status(principal, request, progress):
        if progress is None:
            return None
        if progress.stage == "published":
            outcome = {"status": "published", "derivation": progress.derivation.model_dump(mode="json"),
                       "receipt": progress.receipt.model_dump(mode="json")}
        elif progress.stage == "failed":
            outcome = {"status": "failed", "code": progress.failure, "external_effects": "possible"}
        else:
            outcome = {"status": "pending"}
        return AssessmentPublicationStatus.model_validate_json(json.dumps({"wire_version": "1",
            "request": request.model_dump(mode="json"), "actor_id": principal.actor_id, "outcome": outcome}))

    def read_publication(self, principal, request):
        principal.require("read_assessment_publication", request.scope)
        progress = PublicationStore(self.engine).lookup(request.scope, request.assessment_id, principal.actor_id)
        return self._publication_status(principal, request, progress)

    def publish(self, principal, request):
        principal.require("publish_assessment", request.scope)
        workflow = PublicationWorkflow(PublicationStore(self.engine), self.reader(request.scope),
            HttpTransport(self.endpoint, self.publication_token), self.publisher, self.issuer)
        progress = workflow.submit(request.scope, request.assessment_id, principal.actor_id)
        return self._publication_status(principal, request, progress)
