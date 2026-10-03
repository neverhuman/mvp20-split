"""Closed scientific decision encoding mechanism; policy and dependencies stay with each owner module."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Identifier, Scope
from amphora_contracts_research import (
    EligibilityAssessment,
    EligibilityDecision,
    ScientificDecisionRef,
    SynthesisAssessment,
    SynthesisDecision,
)
from pydantic import TypeAdapter

MODELS = {"eligibility":EligibilityDecision,"synthesis":SynthesisDecision}
IDENTIFIER = TypeAdapter(Identifier)


class DecisionStoreError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise DecisionStoreError(reason)


def canonical(value):
    body = json.dumps(value,sort_keys=True,separators=(",", ":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
    require(len(body) <= 8388608,"scientific_decision_byte_limit")
    return body


@dataclass(frozen=True, slots=True)
class DecisionDocument:
    record: EligibilityDecision | SynthesisDecision
    canonical_bytes: bytes

    @classmethod
    def prepare(cls, kind, scope, actor, decision_id, assessment, sources, observations=()):
        require(kind in MODELS and type(scope) is Scope,"scientific_decision_kind_or_scope")
        expected = EligibilityAssessment if kind == "eligibility" else SynthesisAssessment
        require(type(assessment) is expected,"scientific_decision_assessment_type")
        context = assessment.policy.context
        candidate = context.subject.candidate if kind == "eligibility" else context.candidate
        require(candidate.scope == scope,"scientific_decision_assessment_scope")
        IDENTIFIER.validate_python(actor,strict=True)
        IDENTIFIER.validate_python(decision_id,strict=True)
        # Exact Artifact identities cannot disagree merely because their stable id matches.
        sources = tuple(set(sources))
        require(0 < len(sources) <= 128,"scientific_decision_source_limit")
        require(all(item.scope == scope for item in sources),"scientific_decision_source_scope")
        require(len({item.artifact_id for item in sources}) == len(sources),"scientific_decision_source_conflict")
        sources = tuple(sorted(sources,key=lambda item:item.artifact_id))
        observations = tuple(sorted(set(observations),key=lambda item:(item.observation_id,item.revision)))
        require(len(observations) <= 1024 and all(item.scope == scope for item in observations),"scientific_decision_observation_scope_or_limit")
        fields = {"wire_version":"1","actor_id":actor,"assessment":assessment,"sources":sources}
        if kind == "eligibility":
            fields["observations"] = observations
        else:
            require(not observations,"synthesis_observation_index_not_declared")
        # Hash excludes its own reference, but includes kind/scope/id and the complete policy/result/inputs/actor.
        payload = {"format":"research.scientific-decision.v1","kind":kind,"scope":scope.model_dump(mode="json"),
            "decision_id":decision_id,"actor_id":actor,"assessment":assessment.model_dump(mode="json"),
            "sources":[item.model_dump(mode="json") for item in sources],
            "observations":[item.model_dump(mode="json") for item in observations]}
        reference = ScientificDecisionRef(scope=scope,kind=kind,decision_id=decision_id,sha256=hashlib.sha256(canonical(payload)).hexdigest())
        record = MODELS[kind](reference=reference,**fields)
        record = MODELS[kind].model_validate_json(record.model_dump_json())
        return cls(record,canonical(record.model_dump(mode="json")))

    @property
    def key(self):
        ref = self.record.reference
        return {"tenant":ref.scope.tenant_id,"project":ref.scope.project_id,"kind":ref.kind,"id":ref.decision_id}
