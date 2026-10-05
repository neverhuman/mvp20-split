"""Read immutable Planning origin and accounting; never reserve or settle again."""

from dataclasses import dataclass

from ..budget import BudgetPolicy
from ..budget.charge import BudgetCharge
from ..campaign_decisions import CampaignDecisionReview
from ..campaign_preparations.journal import (
    CampaignPreparationJournal,
    StoredCampaignPreparation,
)
from ..context.policy import require
from ..persistence.budget import BudgetLedger, BudgetReservation
from ..persistence.journal import PlanningJournal
from ..persistence.records import AttemptJournal
from ..persistence.settlement import BudgetSettlement, SettlementJournal


@dataclass(frozen=True)
class StoredCampaignOrigin:
    review: CampaignDecisionReview
    budget: BudgetPolicy
    preparation: StoredCampaignPreparation
    attempt: AttemptJournal
    reservation: BudgetReservation
    settlement: BudgetSettlement

    @classmethod
    def bind(cls, review, budget, preparation, attempt, reservation, settlement):
        verified = CampaignDecisionReview.bind(review.composition.evidence.proposal, review.declaration, budget)
        require(verified == review, 'campaign_origin_review')
        proposal = review.composition.evidence.proposal
        require(preparation is not None and preparation.record == proposal.inputs.preparation,
                'campaign_origin_preparation')
        require(attempt is not None and attempt.binding == proposal.attempt and attempt.observation == proposal.observation,
                'campaign_origin_observation')
        require(reservation is not None and reservation.demand == review.demand, 'campaign_origin_reservation')
        charge = BudgetCharge.reconcile(review.demand, proposal.observation.canonical)
        require(settlement is not None and settlement.charge == charge, 'campaign_origin_settlement')
        return cls(review, budget, preparation, attempt, reservation, settlement)

    def verify(self):
        require(self.bind(self.review, self.budget, self.preparation, self.attempt, self.reservation, self.settlement) == self,
                'campaign_origin_binding')
        return self


class CampaignOriginReader:
    def __init__(self, engine):
        self.preparations = CampaignPreparationJournal(engine)
        self.attempts = PlanningJournal(engine)
        self.budgets = BudgetLedger(engine)
        self.settlements = SettlementJournal(engine)

    def read(self, principal, review, budget):
        reference = review.composition.evidence.proposal.attempt.reference()
        # Each interface enforces original actor/scope. These records are
        # immutable, so separate short reads need no peer-spanning transaction.
        preparation = self.preparations.read(principal, reference.engagement)
        attempt = self.attempts.read_attempt(principal, reference)
        reservation = self.budgets.read(principal, reference)
        settlement = self.settlements.read(principal, reference)
        return StoredCampaignOrigin.bind(review, budget, preparation, attempt, reservation, settlement)
