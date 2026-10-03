"""Pinned owner assessment bytes and purpose-limited receipt policy."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_artifacts import ContentDescriptor, DerivationDeclaration, TransformationDescriptor
from amphora_contracts_core import SchemaRef
from amphora_contracts_graph_runtime import DomainReceipt
from amphora_contracts_research import EvidenceAssessment

from ..assessment.policy import AssessmentError
from ..assessment.store import StoredAssessment, canonical


@dataclass(frozen=True)
class AssessmentArtifact:
    stored: StoredAssessment
    body: bytes
    content: ContentDescriptor
    declaration: DerivationDeclaration

    @staticmethod
    def schema_document():
        schema = EvidenceAssessment.model_json_schema(mode="validation")
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        return canonical(schema, 1048576) + b"\n"

    @classmethod
    def from_stored(cls, stored):
        if stored.resolved is None:
            raise AssessmentError("publication_assessment_pending")
        stored.intent.decision(stored.resolved)
        body = canonical(stored.resolved.assessment.model_dump(mode="json"), 8388608)
        schema = SchemaRef(schema_id="research.evidence-assessment.payload", version="1",
                           sha256=hashlib.sha256(cls.schema_document()).hexdigest())
        content = ContentDescriptor(sha256=hashlib.sha256(body).hexdigest(), size_bytes=len(body),
                                    media_type="application/json", schema_ref=schema)
        profile = stored.intent.bound.configured.reference
        method = canonical({"algorithm_profile": "research.synthetic_sufficiency.v1",
                            "profile": profile.model_dump(mode="json")}, 4096)
        declaration = DerivationDeclaration(transformation=TransformationDescriptor(
            transformation_id="research.synthetic_sufficiency", version="1", sha256=hashlib.sha256(method).hexdigest()),
            inputs=tuple(sorted(stored.resolved.inputs, key=lambda ref: ref.artifact_id)))
        return cls(stored, body, content, declaration)


class SyntheticReceiptPolicy:
    version = "research.synthetic_sufficiency.v1"
    purpose = "research.synthetic_sufficiency"

    @staticmethod
    def disposition(assessment):
        if assessment.sufficient:
            if (not assessment.answered or assessment.disposition != "supported"
                    or any(need.gap is not None for need in assessment.needs)):
                raise AssessmentError("publication_assessment_inconsistent")
            return "accepted", None
        if assessment.disposition == "contradicted":
            return "rejected", "evidence_contradicted"
        return "abstained", "evidence_insufficient"

    def issue(self, artifact, publisher, issuer, derivation):
        assessment = artifact.stored.resolved.assessment
        ref = derivation.artifact
        scope = assessment.request.profile.scope
        if (ref.scope != scope or ref.sha256 != artifact.content.sha256
                or ref.size_bytes != artifact.content.size_bytes or ref.schema_ref != artifact.content.schema_ref
                or ref.media_type != artifact.content.media_type or derivation.declaration != artifact.declaration
                or derivation.origin.actor_id != publisher or derivation.origin.scope != scope
                or derivation.origin.command_family != "artifacts.begin_derived_upload"):
            raise AssessmentError("publication_derivation_mismatch")
        status, reason = self.disposition(assessment)
        outcome = ({"status": "accepted", "output": {"kind": "artifact", "artifact": ref.model_dump(mode="json"),
                    "representation": "research.evidence_assessment.v1", "unit": "1"}}
                   if status == "accepted" else {"status": status, "reason_code": reason})
        identity = canonical({"policy": self.version, "actor": assessment.actor_id,
                              "request": assessment.request.model_dump(mode="json"), "publisher": publisher,
                              "issuer": issuer, "derivation": derivation.model_dump(mode="json")}, 2097152)
        return DomainReceipt.model_validate_json(canonical({"schema_version": "1", "issuer_id": issuer,
            "receipt_id": "research-" + hashlib.sha256(identity).hexdigest(), "scope": scope.model_dump(mode="json"),
            "purpose": self.purpose, "revision": "1", "subject": assessment.subject.model_dump(mode="json"),
            "outcome": outcome}, 2097152))
