"""Only explicit action prerequisites determine eligibility; weaknesses remain inspectable."""
from dataclasses import dataclass
from typing import ClassVar

from amphora_contracts_core import SchemaRef

from .evidence import KINDS, CriterionClaim, DecisionContext, identifier, names, require


@dataclass(frozen=True, slots=True)
class Requirement:
    criterion_id: str
    kind: str
    method: SchemaRef
    required: bool
    excluded_flags: tuple[str, ...]

    def __post_init__(self):
        identifier(self.criterion_id)
        require(self.kind in KINDS,"invalid_eligibility_kind")
        require(type(self.method) is SchemaRef,"eligibility_method_required")
        require(type(self.required) is bool,"explicit_requirement_mode_required")
        names(self.excluded_flags)


@dataclass(frozen=True, slots=True)
class ClaimReview:
    claim: CriterionClaim
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CriterionDecision:
    requirement: Requirement
    disposition: str
    reason: str
    reviews: tuple[ClaimReview, ...]


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    policy: SchemaRef
    context: DecisionContext
    disposition: str
    criteria: tuple[CriterionDecision, ...]
    reviews: tuple[ClaimReview, ...]
    authority: ClassVar[str] = "synthetic"

    @property
    def focus(self):
        return tuple(item.requirement.criterion_id for item in self.criteria if item.disposition != "supported"
                     or any(review.claim.flags or review.reasons for review in item.reviews))


@dataclass(frozen=True, slots=True)
class EligibilityPolicy:
    reference: SchemaRef
    context: DecisionContext
    requirements: tuple[Requirement, ...]
    authority: ClassVar[str] = "synthetic"

    def __post_init__(self):
        require(type(self.reference) is SchemaRef,"eligibility_policy_reference_required")
        require(type(self.context) is DecisionContext,"decision_context_required")
        require(type(self.requirements) is tuple and 1 <= len(self.requirements) <= 128,"eligibility_requirement_bound")
        require(all(type(item) is Requirement for item in self.requirements),"eligibility_requirement_required")
        require(len({item.criterion_id for item in self.requirements}) == len(self.requirements),"duplicate_eligibility_requirement")

    def assess(self, claims):
        require(type(claims) is tuple and len(claims) <= 1024,"eligibility_claim_bound")
        require(all(type(item) is CriterionClaim for item in claims),"criterion_claim_required")
        keys = tuple((item.criterion_id,item.origin.source.scope,item.origin.source.artifact_id,item.origin.observation) for item in claims)
        require(len(set(keys)) == len(keys),"duplicate_criterion_source")
        reviews = tuple(self._review(item) for item in claims)
        criteria = tuple(self._decide(requirement,reviews) for requirement in self.requirements)
        hard = {item.disposition for item in criteria if item.requirement.required}
        disposition = "ineligible" if "contradicted" in hard else "unknown" if "unknown" in hard else "eligible"
        return EligibilityDecision(self.reference,self.context,disposition,criteria,reviews)

    def _review(self, claim):
        reasons = []
        if claim.context != self.context:
            reasons.append("applicability_mismatch")
        if claim.origin.authority != self.authority:
            reasons.append("authority_mismatch")
        requirement = next((item for item in self.requirements if item.criterion_id == claim.criterion_id),None)
        if requirement is None:
            reasons.append("undeclared_criterion")
        else:
            if claim.origin.kind != requirement.kind:
                reasons.append("evidence_kind_mismatch")
            if claim.origin.method != requirement.method:
                reasons.append("method_mismatch")
            if set(claim.flags) & set(requirement.excluded_flags):
                reasons.append("quality_excluded_by_policy")
        return ClaimReview(claim,tuple(reasons))

    @staticmethod
    def _decide(requirement, reviews):
        relevant = tuple(item for item in reviews if item.claim.criterion_id == requirement.criterion_id)
        accepted = {item.claim.disposition for item in relevant if not item.reasons}
        if {"supported","contradicted"} <= accepted:
            disposition,reason = "unknown","conflicting_evidence"
        elif "unknown" in accepted:
            disposition,reason = "unknown","explicit_uncertainty"
        elif "contradicted" in accepted:
            disposition,reason = "contradicted","prerequisite_failed"
        elif "supported" in accepted:
            disposition,reason = "supported","bounded_support"
        else:
            disposition,reason = "unknown","missing_eligible_evidence"
        return CriterionDecision(requirement,disposition,reason,relevant)
