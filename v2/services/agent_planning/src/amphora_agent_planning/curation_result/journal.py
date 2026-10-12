"""Read immutable attempt/accounting before a short fenced progress transaction."""
from amphora_contracts_campaign_curation import CurationView
from ..context import AttemptBinding
from ..context.policy import require
from ..curation_jobs.journal import CurationJobs, key_for, current
from ..curation_jobs.state import JobProgress
from ..curation_preparation.link import CurationPreparationJournal
from ..persistence.journal import PlanningJournal
from ..persistence.budget import BudgetLedger
from ..persistence.settlement import SettlementJournal
from .outcome import ProviderOutcome


class CurationResultJournal:
    def __init__(self, engine):
        self.engine = engine
        self.jobs = CurationJobs(engine)
        self.inputs = CurationPreparationJournal(engine)
        self.attempts = PlanningJournal(engine)
        self.budgets = BudgetLedger(engine)
        self.settlements = SettlementJournal(engine)

    def read(self, principal, curation_id):
        principal.require('execute_curations', principal.scope)
        recovered = self.inputs.recover(principal, curation_id)
        require(recovered is not None and recovered.link is not None, 'curation_result_input')
        frozen = recovered.link.frozen
        reference = AttemptBinding(frozen.preparation.packet.request, 1).reference()
        attempt = self.attempts.read_attempt(principal, reference)
        if attempt is None or attempt.observation is None:
            return None
        return ProviderOutcome.bind(recovered.original.incoming, frozen, attempt,
            self.budgets.read(principal, reference), self.settlements.read(principal, reference))

    def record(self, principal, lease):
        outcome = self.read(principal, lease.curation_id)
        require(outcome is not None, 'curation_result_pending')
        key = key_for(principal, lease.curation_id)
        with self.engine.begin() as conn:
            self.jobs._lock(conn, key)
            original = self.jobs._original(conn, principal, key)
            previous = current(conn, original)
            if previous is not None and previous.view.provider is not None:
                require(previous.view.provider == outcome.provider and previous.view.proposal == outcome.proposal,
                        'curation_result_conflict')
                return previous
            previous, at = self.jobs._owned(conn, principal, lease, key)
            require(previous.view.receipt.phase == 'awaiting_provider', 'curation_result_phase')
            phase, reason = outcome.disposition
            receipt = previous.view.receipt.model_copy(update={'phase': phase, 'reason_code': reason,
                'revision': previous.view.receipt.revision + 1, 'updated_at': at})
            view = CurationView.model_validate_json(previous.view.model_copy(update={
                'receipt': receipt, 'provider': outcome.provider, 'proposal': outcome.proposal}).model_dump_json())
            progress = JobProgress(original, view)
            self.jobs._append(conn, key, progress)
            return progress
