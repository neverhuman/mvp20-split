"""Eligibility wire output is projected from owner policy; input verdicts are not accepted."""
from amphora_contracts_research import (
    EligibilityAssessment,
    EligibilityClaim,
    EligibilityClaimReview,
    EligibilityContext,
    EligibilityCriterionDecision,
    EligibilityEvidenceOrigin,
    EligibilityProfile,
    EligibilityRequirement,
    EligibilitySubject,
)

from ..observations.wire import reference_from_wire, reference_to_wire
from .evidence import CriterionClaim, DecisionContext, DecisionSubject, EvidenceOrigin
from .policy import EligibilityPolicy, Requirement


def context_to_wire(value):
    return EligibilityContext(subject=EligibilitySubject(candidate=value.subject.candidate,
        material_state=value.subject.material_state,sample=value.subject.sample),domain=value.domain,
        purpose=value.purpose,conditions=value.conditions)


def context_from_wire(record):
    return DecisionContext(DecisionSubject(record.subject.candidate,record.subject.material_state,record.subject.sample),
                           record.domain,record.purpose,record.conditions)


def claim_to_wire(value):
    origin = value.origin
    return EligibilityClaim(criterion_id=value.criterion_id,context=context_to_wire(value.context),
        origin=EligibilityEvidenceOrigin(source=origin.source,method=origin.method,kind=origin.kind,authority=origin.authority,
                                        observation=reference_to_wire(origin.observation)),disposition=value.disposition,flags=value.flags)


def claim_from_wire(record):
    origin = record.origin
    return CriterionClaim(record.criterion_id,context_from_wire(record.context),
        EvidenceOrigin(origin.source,origin.method,origin.kind,origin.authority,reference_from_wire(origin.observation)),
        record.disposition,record.flags)


def profile_to_wire(policy):
    return EligibilityProfile(wire_version="1",authority=policy.authority,reference=policy.reference,context=context_to_wire(policy.context),
        requirements=tuple(EligibilityRequirement(criterion_id=item.criterion_id,kind=item.kind,method=item.method,
            required=item.required,excluded_flags=item.excluded_flags) for item in policy.requirements))


def profile_from_wire(record):
    return EligibilityPolicy(record.reference,context_from_wire(record.context),
        tuple(Requirement(item.criterion_id,item.kind,item.method,item.required,item.excluded_flags) for item in record.requirements))


def assess_to_wire(policy, claims):
    decision = policy.assess(claims)
    return EligibilityAssessment(wire_version="1",authority=decision.authority,policy=profile_to_wire(policy),disposition=decision.disposition,
        criteria=tuple(EligibilityCriterionDecision(criterion_id=item.requirement.criterion_id,disposition=item.disposition,
            reason=item.reason) for item in decision.criteria),
        reviews=tuple(EligibilityClaimReview(claim=claim_to_wire(item.claim),reasons=item.reasons) for item in decision.reviews),
        focus=decision.focus)
