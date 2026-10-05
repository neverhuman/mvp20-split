"""Reconstruct compiler selection authority from immutable Planning-owned history."""

from dataclasses import dataclass

from ..budget import BudgetPolicy
from ..campaign_authoring import AuthoringPlan
from ..campaign_decisions import CampaignDecisionReview, DecisionDeclaration
from ..campaign_eligibility import EligibilityConfiguration
from ..campaign_handoff import CampaignOriginReader, StoredCampaignOrigin
from ..campaign_proposals import PreparedCampaignProposal
from ..context.policy import require
from .selection import CompilerSelection


@dataclass(frozen=True)
class CompilerHistory:
    origin: StoredCampaignOrigin
    authoring: AuthoringPlan
    eligibility: EligibilityConfiguration

    @classmethod
    def load(cls, engine, principal, selection):
        selection = CompilerSelection.restore(selection.canonical, principal)
        value = selection.document()
        reader = CampaignOriginReader(engine)
        reference = value.origin.attempt
        preparation = reader.preparations.read(principal, reference.engagement)
        attempt = reader.attempts.read_attempt(principal, reference)
        require(preparation is not None and attempt is not None and attempt.observation is not None,
                'compiler_origin_incomplete')
        proposal = PreparedCampaignProposal.bind(preparation.record, attempt.binding, attempt.observation)
        declaration = DecisionDeclaration.from_bytes(value.witness.declaration_json.encode())
        budget = BudgetPolicy.from_bytes(value.witness.budget_json.encode())
        review = CampaignDecisionReview.bind(proposal, declaration, budget)
        origin = StoredCampaignOrigin.bind(review, budget, preparation, attempt,
            reader.budgets.read(principal, reference), reader.settlements.read(principal, reference))
        authoring = AuthoringPlan.bind(review, budget, owner_id=value.runtime.owner_id, actor_id=value.runtime.actor_id)
        eligibility = EligibilityConfiguration(value.witness.eligibility_json.encode())
        selection.verify_origin(principal, authoring, eligibility)
        return cls(origin, authoring, eligibility)
