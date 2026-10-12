"""Durable provider evidence, distinct from compiler or scientific acceptance."""
from dataclasses import dataclass
from amphora_contracts_campaign_curation import CurationProviderRecord
from ..budget.charge import BudgetCharge
from ..context import AttemptBinding
from ..context.policy import require
from ..curation_output import CurationOutput
from ..curation_preparation.link import FrozenInput
from ..persistence.records import verified_observation, AttemptJournal
from ..persistence.budget import BudgetReservation
from ..persistence.settlement import BudgetSettlement


@dataclass(frozen=True)
class ProviderOutcome:
    frozen: FrozenInput
    attempt: AttemptJournal
    reservation: BudgetReservation
    settlement: BudgetSettlement

    @classmethod
    def bind(cls, incoming, frozen, attempt, reservation, settlement):
        frozen = FrozenInput.bind(incoming, frozen.preparation)
        binding = AttemptBinding(frozen.preparation.packet.request, 1)
        require(attempt is not None and attempt.binding == binding and attempt.observation is not None,
                'curation_result_observation')
        verified_observation(binding, attempt.observation)
        require(reservation is not None and reservation.demand.attempt == binding.reference(),
                'curation_result_reservation')
        charge = BudgetCharge.reconcile(reservation.demand, attempt.observation.canonical)
        require(settlement is not None and settlement.charge == charge, 'curation_result_settlement')
        return cls(frozen, attempt, reservation, settlement)

    @property
    def proposal(self):
        observed = self.attempt.observation
        if observed.document().proposal is None:
            return None
        return CurationOutput.parse(observed.capture.content, self.attempt.binding.request).document()

    @property
    def provider(self):
        observed = self.attempt.observation
        return CurationProviderRecord(attempt=self.attempt.binding.reference(),
            envelope_sha256=self.frozen.envelope.sha256, output_sha256=observed.capture.sha256,
            usage=observed.document().usage, reservation_units=self.reservation.demand.accounting_units)

    @property
    def disposition(self):
        if self.settlement.charge.overage:
            return 'failed', 'provider_usage_overage'
        proposal = self.proposal
        if proposal is not None:
            kind = proposal.outcome.kind
            return {'propose_campaign': ('proposed', 'provider_proposal'),
                    'request_capabilities': ('proposed', 'capabilities_requested'),
                    'abstain': ('abstained', 'provider_abstained')}[kind]
        return {'unknown': ('indeterminate', 'provider_outcome_unknown'),
                'unavailable': ('failed', 'provider_unavailable'),
                'invalid': ('failed', 'model_output_invalid'),
                'policy_rejected': ('failed', 'model_output_rejected')}[self.attempt.observation.document().status]
