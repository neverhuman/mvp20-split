"""Route evidence posture is independent from project executability."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, SchemaRef
from amphora_contracts_research import CandidateRevisionRef

from ..observations import Quantity
from .validation import bounded, identifier, names, require

POSTURES = ("unassessed","proposed","precedent_supported","documented_target","demonstrated","no_route_found")


@dataclass(frozen=True, slots=True)
class SynthesisContext:
    candidate: CandidateRevisionRef
    domain: str
    purpose: str
    conditions: ArtifactRef
    scale: Quantity | None
    purity: ArtifactRef | None

    def __post_init__(self):
        require(type(self.candidate) is CandidateRevisionRef,"synthesis_candidate_required")
        identifier(self.domain)
        identifier(self.purpose)
        require(type(self.conditions) is ArtifactRef,"synthesis_conditions_required")
        require(self.scale is None or type(self.scale) is Quantity,"synthesis_scale_type")
        if self.scale is not None:
            require(self.scale.value.amount > 0,"synthesis_scale_positive")
        require(self.purity is None or type(self.purity) is ArtifactRef,"synthesis_purity_type")
        require(all(ref.scope == self.candidate.scope for ref in (self.conditions,self.purity) if ref is not None),
                "synthesis_context_scope_mismatch")


@dataclass(frozen=True, slots=True)
class RouteProvenance:
    method: SchemaRef
    tool: SchemaRef
    models: tuple[SchemaRef, ...]
    sources: tuple[ArtifactRef, ...]

    def __post_init__(self):
        require(type(self.method) is SchemaRef and type(self.tool) is SchemaRef,"route_method_tool_required")
        bounded(self.models,SchemaRef,32,"route_model_bound")
        bounded(self.sources,ArtifactRef,128,"route_source_bound")
        require(len(set(self.models)) == len(self.models),"duplicate_route_model")
        require(len(set(self.sources)) == len(self.sources),"duplicate_route_source")


@dataclass(frozen=True, slots=True)
class RouteStep:
    step_id: str
    requires: tuple[str, ...]
    posture: str
    record: ArtifactRef
    sources: tuple[ArtifactRef, ...]
    gaps: tuple[str, ...]

    def __post_init__(self):
        identifier(self.step_id)
        names(self.requires)
        require(self.step_id not in self.requires,"route_step_self_dependency")
        require(self.posture in POSTURES[:-1],"invalid_route_step_posture")
        require(type(self.record) is ArtifactRef,"route_step_record_required")
        bounded(self.sources,ArtifactRef,64,"route_step_source_bound")
        require(self.posture == "unassessed" or bool(self.sources),"route_step_evidence_required")
        names(self.gaps)


@dataclass(frozen=True, slots=True)
class SearchRecord:
    scope: ArtifactRef
    budget: Quantity

    def __post_init__(self):
        require(type(self.scope) is ArtifactRef,"route_search_scope_required")
        require(type(self.budget) is Quantity and self.budget.value.amount > 0,"route_search_budget_positive")


@dataclass(frozen=True, slots=True)
class RouteEvidence:
    context: SynthesisContext
    route: ArtifactRef | None
    posture: str
    provenance: RouteProvenance
    steps: tuple[RouteStep, ...]
    search: SearchRecord | None
    next_checks: tuple[str, ...]

    def __post_init__(self):
        require(type(self.context) is SynthesisContext,"synthesis_context_required")
        require(self.route is None or type(self.route) is ArtifactRef,"route_reference_type")
        require(self.posture in POSTURES,"invalid_route_posture")
        require(type(self.provenance) is RouteProvenance,"route_provenance_required")
        bounded(self.steps,RouteStep,256,"route_step_bound")
        require(self.search is None or type(self.search) is SearchRecord,"route_search_type")
        names(self.next_checks)
        if self.posture in ("unassessed","no_route_found"):
            require(self.route is None and not self.steps,"absent_route_has_steps")
        else:
            require(self.route is not None and bool(self.steps) and bool(self.provenance.sources),"route_evidence_required")
        if self.posture == "no_route_found":
            require(self.search is not None and bool(self.provenance.sources),"bounded_search_required")
        seen = set()
        refs = [self.context.conditions,*self.provenance.sources]
        if self.route is not None:
            refs.append(self.route)
        if self.search is not None:
            refs.append(self.search.scope)
        for step in self.steps:
            require(step.step_id not in seen,"duplicate_route_step")
            require(set(step.requires) <= seen,"route_step_dependency_unresolved")
            seen.add(step.step_id)
            refs.extend((step.record,*step.sources))
        require(all(ref.scope == self.context.candidate.scope for ref in refs),"route_evidence_scope_mismatch")
