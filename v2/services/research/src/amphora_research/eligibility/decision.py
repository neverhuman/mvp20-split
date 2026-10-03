"""Build an immutable eligibility decision from the owned policy, retaining every reviewed claim."""
from ..persistence.decision_document import DecisionDocument
from .wire import assess_to_wire


def prepare(policy, claims, actor, decision_id):
    assessment = assess_to_wire(policy,claims)
    sources = [assessment.policy.context.conditions]
    observations = []
    for review in assessment.reviews:
        claim = review.claim
        sources.extend((claim.context.conditions,claim.origin.source))
        if claim.origin.observation is not None:
            observations.append(claim.origin.observation)
    return DecisionDocument.prepare("eligibility",policy.context.subject.candidate.scope,actor,decision_id,
                                    assessment,sources,observations)
