"""Immutable accepted scientific request/configuration; incomplete work is not a scientific verdict."""
import json
from dataclasses import dataclass

from amphora_contracts_research import (
    EligibilityInputProfile,
    ScientificAssessmentComplete,
    ScientificAssessmentPending,
    ScientificAssessmentRequest,
    ScientificAssessmentStatus,
    SynthesisInputProfile,
)

from .boundary import ConfiguredScientificInput, canonical, require
from .resolution import ResolvedScientificInput


@dataclass(frozen=True, slots=True)
class ScientificIntent:
    bound: object
    content: bytes

    @classmethod
    def prepare(cls, bound):
        configured = ConfiguredScientificInput(bound.configured.document)
        bound = configured.bind(bound.request,bound.actor,configured.scope)
        content = canonical({"format":"research.scientific-intent.v1","request":bound.request.model_dump(mode="json"),
            "profile":configured.document.model_dump(mode="json"),"actor":bound.actor})
        return cls(bound,content)

    @classmethod
    def restore(cls, content):
        raw = json.loads(content)
        require(raw["format"] == "research.scientific-intent.v1","scientific_intent_storage_format")
        kind = raw["profile"]["kind"]
        require(kind in ("eligibility","synthesis"),"scientific_intent_profile_kind")
        model = EligibilityInputProfile if kind == "eligibility" else SynthesisInputProfile
        configured = ConfiguredScientificInput(model.model_validate_json(json.dumps(raw["profile"])))
        request = ScientificAssessmentRequest.model_validate_json(json.dumps(raw["request"]))
        return cls.prepare(configured.bind(request,raw["actor"],configured.scope))

    @property
    def key(self):
        return self.bound.key

    def document(self, resolved):
        require(type(resolved) is ResolvedScientificInput and resolved.bound == self.bound,"scientific_intent_resolution_mismatch")
        inputs = resolved.inputs
        require(type(inputs) is tuple and 0 < len(inputs) <= 128,"scientific_intent_input_limit")
        require(len({item.artifact_id for item in inputs}) == len(inputs),"scientific_intent_input_duplicate")
        require(all(item.scope == self.bound.configured.scope for item in inputs),"scientific_intent_input_scope")
        require(set(self.bound.request.reports) <= set(inputs),"scientific_intent_report_missing")
        document = resolved.decision_document()
        require(set(document.record.sources) <= set(inputs),"scientific_intent_dependency_missing")
        return document

    def status(self, decision=None):
        bound = self.bound
        if decision is None:
            outcome = ScientificAssessmentPending(status="pending")
        else:
            ref = decision.reference
            require(ref.scope == bound.configured.scope and ref.kind == bound.request.profile.kind
                and ref.decision_id == bound.request.decision_id and decision.actor_id == bound.actor
                and decision.assessment.policy == bound.configured.document.policy,"scientific_intent_decision_mismatch")
            outcome = ScientificAssessmentComplete(status="assessed",decision=decision)
        return ScientificAssessmentStatus(wire_version="1",request=bound.request,actor_id=bound.actor,outcome=outcome)
