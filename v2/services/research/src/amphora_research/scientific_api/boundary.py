"""Reviewed profile identity and actor/scope binding, independent of peer I/O and storage."""
import hashlib
import json
from dataclasses import dataclass, field

from amphora_contracts_core import Identifier, Scope
from amphora_contracts_research import (
    EligibilityInputProfile,
    ScientificAssessmentRequest,
    ScientificInputProfileRef,
    SynthesisInputProfile,
)
from pydantic import TypeAdapter

from ..eligibility.wire import profile_from_wire as eligibility_policy
from ..synthesis.wire import profile_from_wire as synthesis_policy

IDENTIFIER = TypeAdapter(Identifier)


class ScientificInputError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise ScientificInputError(reason)


def canonical(value, limit=2097152):
    body = json.dumps(value,sort_keys=True,separators=(",", ":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
    require(len(body) <= limit,"scientific_input_byte_limit")
    return body


@dataclass(frozen=True, slots=True)
class ConfiguredScientificInput:
    document: EligibilityInputProfile | SynthesisInputProfile
    policy: object = field(init=False)

    def __post_init__(self):
        model = type(self.document)
        require(model in (EligibilityInputProfile,SynthesisInputProfile),"scientific_input_profile_type")
        document = model.model_validate_json(self.document.model_dump_json())
        require(len(set(document.publishers)) == len(document.publishers),"scientific_input_duplicate_publisher")
        policy = eligibility_policy(document.policy) if model is EligibilityInputProfile else synthesis_policy(document.policy)
        canonical(document.model_dump(mode="json"))
        object.__setattr__(self,"document",document)
        object.__setattr__(self,"policy",policy)

    @property
    def scope(self):
        context = self.document.policy.context
        return context.subject.candidate.scope if self.document.kind == "eligibility" else context.candidate.scope

    @property
    def reference(self):
        document = self.document
        return ScientificInputProfileRef(scope=self.scope,kind=document.kind,profile_id=document.profile_id,version=document.version,
            sha256=hashlib.sha256(canonical(document.model_dump(mode="json"))).hexdigest())

    def bind(self, request, actor, scope):
        require(type(request) is ScientificAssessmentRequest,"scientific_input_request_type")
        request = ScientificAssessmentRequest.model_validate_json(request.model_dump_json())
        IDENTIFIER.validate_python(actor,strict=True)
        require(type(scope) is Scope and scope == self.scope and request.profile.scope == scope,"scientific_input_scope_mismatch")
        require(request.profile == self.reference,"scientific_input_profile_mismatch")
        require(all(reference.scope == scope for reference in request.reports),"scientific_input_report_scope")
        require(len({reference.artifact_id for reference in request.reports}) == len(request.reports),"scientific_input_duplicate_report")
        return BoundScientificAssessment(self,request,actor)


@dataclass(frozen=True, slots=True)
class BoundScientificAssessment:
    configured: ConfiguredScientificInput
    request: ScientificAssessmentRequest
    actor: str

    @property
    def key(self):
        reference = self.request.profile
        return {"tenant":reference.scope.tenant_id,"project":reference.scope.project_id,
                "kind":reference.kind,"id":self.request.decision_id}
