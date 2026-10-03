"""One bounded authenticated scientific input resolution; no owner SQL or inferred source trust."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_research import (
    EligibilityClaim,
    EligibilityEvidenceOrigin,
    SyntheticEligibilityReport,
    SyntheticSynthesisReport,
    synthetic_scientific_report_schema,
)

from ..assessment.resolution import payload, require_inputs
from ..eligibility.decision import prepare as eligibility_decision
from ..eligibility.wire import claim_from_wire
from ..synthesis.decision import context_sources, option_sources
from ..synthesis.decision import prepare as synthesis_decision
from ..synthesis.wire import option_from_wire
from .boundary import BoundScientificAssessment, require


@dataclass(frozen=True, slots=True)
class ResolvedScientificInput:
    bound: BoundScientificAssessment
    evidence: tuple
    inputs: tuple[ArtifactRef, ...]

    def decision_document(self):
        bound = self.bound
        prepare = eligibility_decision if bound.request.profile.kind == "eligibility" else synthesis_decision
        return prepare(bound.configured.policy,self.evidence,bound.actor,bound.request.decision_id,consumed=self.inputs)


class ScientificInputResolver:
    def __init__(self, reader):
        self.reader = reader

    def resolve(self, bound):
        require(type(bound) is BoundScientificAssessment,"scientific_input_bound_required")
        bound = bound.configured.bind(bound.request,bound.actor,bound.configured.scope)
        require(self.reader.scope == bound.configured.scope,"scientific_input_reader_scope")
        require(not self.reader.consumed,"scientific_input_reader_reused")
        profile = bound.configured.document
        kind = profile.kind
        for source in bound.request.reports:
            require(source.schema_ref == synthetic_scientific_report_schema(kind) and source.media_type == "application/json",
                    "scientific_report_schema_mismatch")
            require(source.size_bytes <= 8388608,"scientific_report_byte_limit")
        policy_sources = ((profile.policy.context.conditions,) if kind == "eligibility" else context_sources(profile.policy.context))
        for source in policy_sources:
            self.reader.read(source)
        evidence = []
        for source in bound.request.reports:
            content,proof = self.reader.published(source,frozenset(profile.publishers))
            report = payload(SyntheticEligibilityReport if kind == "eligibility" else SyntheticSynthesisReport,content)
            require(report.issuer == proof.origin.actor_id,"scientific_report_issuer_mismatch")
            require(report.adapter == profile.adapter,"scientific_report_adapter_mismatch")
            method = proof.declaration.transformation
            require((method.transformation_id,method.version,method.sha256) ==
                    (profile.adapter.schema_id,profile.adapter.version,profile.adapter.sha256),"scientific_report_method_mismatch")
            required = [report.raw_report]
            if kind == "eligibility":
                for row in report.claims:
                    origin = row.origin
                    required.append(row.context.conditions)
                    if origin.source is not None:
                        required.append(origin.source)
                    claim = EligibilityClaim(criterion_id=row.criterion_id,context=row.context,disposition=row.disposition,flags=row.flags,
                        origin=EligibilityEvidenceOrigin(source=source if origin.source is None else origin.source,
                            method=origin.method,kind=origin.kind,authority=origin.authority,observation=origin.observation))
                    evidence.append(claim_from_wire(claim))
            else:
                for option in report.options:
                    required.extend(option_sources(option))
                    evidence.append(option_from_wire(option))
            require(all(item.scope == bound.configured.scope for item in required),"scientific_report_source_scope")
            require_inputs(proof,required)
            for reference in dict.fromkeys(required):
                self.reader.read(reference)
            require(len(evidence) <= (1024 if kind == "eligibility" else 64),"scientific_report_evidence_limit")
        return ResolvedScientificInput(bound,tuple(evidence),self.reader.consumed)
