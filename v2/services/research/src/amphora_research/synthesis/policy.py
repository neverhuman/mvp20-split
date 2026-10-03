"""Explicit synthetic project gates preserve alternatives and unknown evidence."""
from dataclasses import dataclass
from typing import ClassVar

from amphora_contracts_core import ArtifactRef, SchemaRef

from .evidence import POSTURES, RouteEvidence, SynthesisContext
from .validation import bounded, identifier, names, require


@dataclass(frozen=True, slots=True)
class ExecutionCheck:
    criterion_id: str
    disposition: str
    evidence: tuple[ArtifactRef, ...]
    reasons: tuple[str, ...]

    def __post_init__(self):
        identifier(self.criterion_id)
        require(self.disposition in ("met","failed","unknown"),"invalid_execution_check")
        bounded(self.evidence,ArtifactRef,64,"execution_evidence_bound")
        require(self.disposition == "unknown" or bool(self.evidence),"execution_evidence_required")
        names(self.reasons)
        require(bool(self.reasons),"execution_reason_required")


@dataclass(frozen=True, slots=True)
class RouteOption:
    evidence: RouteEvidence
    checks: tuple[ExecutionCheck, ...]

    def __post_init__(self):
        require(type(self.evidence) is RouteEvidence,"route_evidence_required")
        bounded(self.checks,ExecutionCheck,128,"execution_check_bound")
        require(len({c.criterion_id for c in self.checks}) == len(self.checks),"duplicate_execution_check")
        require(all(ref.scope == self.evidence.context.candidate.scope for check in self.checks for ref in check.evidence),
                "execution_evidence_scope_mismatch")


@dataclass(frozen=True, slots=True)
class RouteDecision:
    policy: SchemaRef
    option: RouteOption
    disposition: str
    blockers: tuple[str, ...]
    gaps: tuple[str, ...]
    authority: ClassVar[str] = "synthetic"


@dataclass(frozen=True, slots=True)
class SynthesisPolicy:
    reference: SchemaRef
    context: SynthesisContext
    allowed_postures: tuple[str, ...]
    allowed_step_postures: tuple[str, ...]
    required_checks: tuple[str, ...]
    authority: ClassVar[str] = "synthetic"

    def __post_init__(self):
        require(type(self.reference) is SchemaRef,"synthesis_policy_reference_required")
        require(type(self.context) is SynthesisContext,"synthesis_context_required")
        names(self.allowed_postures)
        require(bool(self.allowed_postures) and set(self.allowed_postures) <= set(POSTURES[1:-1]),"invalid_allowed_route_posture")
        names(self.allowed_step_postures)
        require(bool(self.allowed_step_postures) and set(self.allowed_step_postures) <= set(POSTURES[:-1]),"invalid_allowed_step_posture")
        names(self.required_checks,128)
        require(bool(self.required_checks),"explicit_execution_checks_required")

    def assess(self, option):
        require(type(option) is RouteOption,"route_option_required")
        require(option.evidence.context == self.context,"route_policy_context_mismatch")
        checks = {item.criterion_id:item for item in option.checks}
        blockers = tuple(name for name in self.required_checks if name in checks and checks[name].disposition == "failed")
        gaps = tuple(name for name in self.required_checks if name not in checks or checks[name].disposition == "unknown")
        if option.evidence.posture not in self.allowed_postures:
            gaps += ("route_evidence_requirement_unmet",)
        gaps += tuple("step_evidence:"+step.step_id for step in option.evidence.steps
                      if step.posture not in self.allowed_step_postures)
        disposition = "blocked" if blockers else "unknown" if gaps else "eligible"
        return RouteDecision(self.reference,option,disposition,blockers,gaps)

    def assess_alternatives(self, options):
        bounded(options,RouteOption,64,"route_option_bound")
        require(bool(options),"route_options_required")
        routes = tuple(item.evidence.route for item in options)
        require(len(set(routes)) == len(routes),"duplicate_route_option")
        return tuple(self.assess(option) for option in options)
