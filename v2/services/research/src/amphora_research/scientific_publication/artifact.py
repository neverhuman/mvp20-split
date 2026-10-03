"""Typed scientific payloads and exact provenance; no DomainReceipt issuance."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_artifacts import ContentDescriptor, DerivationDeclaration, TransformationDescriptor
from amphora_contracts_core import SchemaRef
from amphora_contracts_research import EligibilityDecision, LabIntakeStatus, SynthesisDecision

MODELS = {"lab-intake":LabIntakeStatus,"eligibility":EligibilityDecision,"synthesis":SynthesisDecision}


class ScientificPublicationError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise ScientificPublicationError(reason)


def canonical(value, limit=8388608):
    body = json.dumps(value,sort_keys=True,separators=(",", ":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
    require(len(body) <= limit,"science_publication_byte_limit")
    return body


@dataclass(frozen=True, slots=True)
class ScientificArtifact:
    kind: str
    record_id: str
    document: object
    body: bytes
    content: ContentDescriptor
    declaration: DerivationDeclaration

    @property
    def scope(self):
        return self.document.request.profile.scope if self.kind == "lab-intake" else self.document.reference.scope

    @property
    def key(self):
        return {"tenant":self.scope.tenant_id,"project":self.scope.project_id,"kind":self.kind,"id":self.record_id}

    @staticmethod
    def schema_document(kind):
        require(kind in MODELS,"science_publication_kind")
        schema = MODELS[kind].model_json_schema(mode="validation")
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        return canonical(schema,1048576)+b"\n"

    @classmethod
    def from_intake(cls, stored):
        require(stored.terminal is not None and stored.status.outcome.status == "resolved","science_intake_not_resolved")
        return cls._prepare("lab-intake",stored.intent.request.intake_id,stored.status,stored.terminal.inputs)

    @classmethod
    def from_decision(cls, decision):
        require(type(decision) in (EligibilityDecision,SynthesisDecision),"science_decision_required")
        kind = "eligibility" if type(decision) is EligibilityDecision else "synthesis"
        require(decision.reference.kind == kind,"science_decision_kind_mismatch")
        return cls._prepare(kind,decision.reference.decision_id,decision,decision.sources)

    @classmethod
    def _prepare(cls, kind, record_id, document, sources):
        document = MODELS[kind].model_validate_json(document.model_dump_json())
        body = canonical(document.model_dump(mode="json"))
        schema = SchemaRef(schema_id="research."+kind+".payload",version="1",sha256=hashlib.sha256(cls.schema_document(kind)).hexdigest())
        content = ContentDescriptor(sha256=hashlib.sha256(body).hexdigest(),size_bytes=len(body),media_type="application/json",schema_ref=schema)
        identity = canonical({"profile":"research.scientific-artifact.v1","kind":kind,"record_id":record_id,
                              "payload_sha256":content.sha256})
        declaration = DerivationDeclaration(transformation=TransformationDescriptor(transformation_id="research.scientific-artifact",
            version="1",sha256=hashlib.sha256(identity).hexdigest()),inputs=tuple(sorted(sources,key=lambda ref:ref.artifact_id)))
        return cls(kind,record_id,document,body,content,declaration)

    def verify_derivation(self, publisher, derivation):
        ref = derivation.artifact
        require(ref.scope == self.scope and ref.sha256 == self.content.sha256 and ref.size_bytes == self.content.size_bytes
            and ref.media_type == self.content.media_type and ref.schema_ref == self.content.schema_ref
            and derivation.declaration == self.declaration and derivation.origin.scope == self.scope
            and derivation.origin.actor_id == publisher,"science_derivation_mismatch")
