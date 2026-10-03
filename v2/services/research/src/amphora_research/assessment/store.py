"""Private append-only assessment journal; no network operations or automatic retries."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_research import (
    EvidenceAssessment,
    EvidenceAssessmentProfile,
    EvidenceAssessmentRequest,
)
from sqlalchemy import Engine, text

from .boundary import BoundAssessment, ConfiguredAssessment
from .policy import AssessmentError
from .resolution import ResolvedAssessment


def canonical(value, limit):
    content = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(content) > limit:
        raise AssessmentError("assessment_record_limit")
    return content


@dataclass(frozen=True)
class AssessmentIntent:
    bound: BoundAssessment
    content: bytes

    @classmethod
    def bind(cls, bound: BoundAssessment):
        configured = ConfiguredAssessment.from_wire(bound.configured.document)
        validated = configured.bind(bound.request, bound.actor_id, configured.reference.scope)
        content = canonical({"format": "research.assessment-intent.v1", "actor_id": validated.actor_id,
                             "request": validated.request.model_dump(mode="json"),
                             "profile": configured.document.model_dump(mode="json")}, 2097152)
        return cls(validated, content)

    @classmethod
    def restore(cls, content):
        raw = json.loads(content)
        if raw["format"] != "research.assessment-intent.v1":
            raise AssessmentError("assessment_storage_format")
        configured = ConfiguredAssessment.from_wire(EvidenceAssessmentProfile.model_validate_json(
            json.dumps(raw["profile"])))
        request = EvidenceAssessmentRequest.model_validate_json(json.dumps(raw["request"]))
        return cls.bind(configured.bind(request, raw["actor_id"], configured.reference.scope))

    @property
    def key(self):
        scope = self.bound.request.profile.scope
        return {"tenant": scope.tenant_id, "project": scope.project_id,
                "id": self.bound.request.assessment_id}

    def decision(self, resolved: ResolvedAssessment):
        result, profile = resolved.assessment, self.bound.configured.document
        if (result.request != self.bound.request or result.actor_id != self.bound.actor_id
                or result.subject != profile.subject or result.purpose != profile.purpose):
            raise AssessmentError("assessment_decision_mismatch")
        scope = self.bound.request.profile.scope
        inputs = resolved.inputs
        if not inputs or len(inputs) > 128:
            raise AssessmentError("assessment_input_limit")
        if any(item.scope != scope for item in inputs):
            raise AssessmentError("assessment_input_scope")
        if len({item.artifact_id for item in inputs}) != len(inputs):
            raise AssessmentError("assessment_input_duplicate")
        required = {profile.subject, profile.question.applicability,
                    *(item.need.required_context for item in profile.requirements),
                    *(item.artifact for item in self.bound.request.answers), *self.bound.request.receipts}
        if not required <= set(inputs):
            raise AssessmentError("assessment_input_missing")
        normalized = tuple(sorted(inputs, key=lambda item: item.artifact_id))
        content = canonical({"format": "research.assessment-decision.v1",
                             "assessment": result.model_dump(mode="json"),
                             "inputs": [item.model_dump(mode="json") for item in normalized]}, 8388608)
        return content


@dataclass(frozen=True)
class StoredAssessment:
    intent: AssessmentIntent
    resolved: ResolvedAssessment | None


class AssessmentStore:
    def __init__(self, engine: Engine):
        self.engine = engine

    @staticmethod
    def _lock(connection, key):
        encoded = canonical(["research-assessment", key["tenant"], key["project"], key["id"]], 4096)
        lock = int.from_bytes(hashlib.sha256(encoded).digest()[:8], "big", signed=True)
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})

    @staticmethod
    def _read(connection, key, *, decision=False):
        table = "assessment_decisions" if decision else "assessment_intents"
        return connection.execute(text(f"SELECT canonical_bytes FROM research.{table} WHERE "
            "tenant_id=:tenant AND project_id=:project AND assessment_id=:id"), key).scalar_one_or_none()

    @staticmethod
    def _insert(connection, key, content, *, decision=False):
        table = "assessment_decisions" if decision else "assessment_intents"
        connection.execute(text(f"INSERT INTO research.{table} "
            "(tenant_id,project_id,assessment_id,canonical_bytes) VALUES (:tenant,:project,:id,:body)"),
            key | {"body": content})

    def begin(self, bound: BoundAssessment) -> AssessmentIntent:
        intent = AssessmentIntent.bind(bound)
        with self.engine.begin() as connection:
            self._lock(connection, intent.key)
            prior = self._read(connection, intent.key)
            if prior is None:
                self._insert(connection, intent.key, intent.content)
            elif bytes(prior) != intent.content:
                raise AssessmentError("assessment_identity_conflict")
        return intent

    def complete(self, bound: BoundAssessment, resolved: ResolvedAssessment) -> StoredAssessment:
        intent = AssessmentIntent.bind(bound)
        content = intent.decision(resolved)
        with self.engine.begin() as connection:
            self._lock(connection, intent.key)
            prior = self._read(connection, intent.key)
            if prior is None:
                raise AssessmentError("assessment_intent_missing")
            if bytes(prior) != intent.content:
                raise AssessmentError("assessment_identity_conflict")
            terminal = self._read(connection, intent.key, decision=True)
            if terminal is None:
                self._insert(connection, intent.key, content, decision=True)
            elif bytes(terminal) != content:
                raise AssessmentError("assessment_decision_conflict")
        return self._restore(intent, content)

    @staticmethod
    def _restore(intent, content):
        if content is None:
            return StoredAssessment(intent, None)
        raw = json.loads(content)
        if raw["format"] != "research.assessment-decision.v1":
            raise AssessmentError("assessment_storage_format")
        result = EvidenceAssessment.model_validate_json(json.dumps(raw["assessment"]))
        inputs = tuple(ArtifactRef.model_validate_json(json.dumps(item)) for item in raw["inputs"])
        resolved = ResolvedAssessment(result, inputs)
        intent.decision(resolved)
        return StoredAssessment(intent, resolved)

    def read(self, scope: Scope, assessment_id: str, actor_id: str) -> StoredAssessment | None:
        key = {"tenant": scope.tenant_id, "project": scope.project_id, "id": assessment_id}
        with self.engine.connect() as connection:
            content = self._read(connection, key)
            if content is None:
                return None
            intent = AssessmentIntent.restore(bytes(content))
            if intent.bound.actor_id != actor_id:
                raise AssessmentError("assessment_actor_mismatch")
            terminal = self._read(connection, key, decision=True)
        return self._restore(intent, None if terminal is None else bytes(terminal))
