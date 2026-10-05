"""Current processing/input checks derive from owned original compiler history."""

from dataclasses import dataclass

from ..campaign_eligibility import EligibilityBatch
from ..campaign_handoff import (
    CampaignOriginReader,
    CompilerPreparation,
    CompilerPreparer,
)
from ..campaign_refresh import RefreshPlan, RefreshResult
from ..context.policy import require


@dataclass(frozen=True)
class DispatchPrerequisites:
    status: str
    detail: CompilerPreparation | RefreshResult | None = None


class CompilerPrerequisites:
    def __init__(self, journal, refresh):
        self.journal, self.refresh = journal, refresh
        self.preparer = CompilerPreparer(CampaignOriginReader(journal.store.engine), refresh)

    def check(self, principal, lease, operation, check_id=None):
        history = self.journal.context(principal, lease.selection).history
        if operation.effect.document().kind == 'resolve':
            # Eligibility cannot be required before issuing that same check.
            self.preparer.origin.read(principal, history.authoring.review, history.authoring.budget)
            plan = RefreshPlan.bind(history.authoring.review, history.authoring.budget)
            result = self.refresh.collect(plan)
            require(result.plan == plan, 'compiler_dispatch_refresh')
            status = 'input_unavailable' if result.failures else 'relevant_input_changed' if result.changes else 'ready_to_journal'
            return DispatchPrerequisites(status, result)
        batch = EligibilityBatch.bind(history.authoring.review, history.authoring.budget,
                                      history.eligibility, 'zero-tools' if check_id is None else check_id)
        observations = ()
        if batch.requests:
            if check_id is None:
                return DispatchPrerequisites('dependency_unavailable')
            current = self.journal.read_round(principal, lease.selection.effect_id, check_id)
            if current is None or not current.terminal:
                return DispatchPrerequisites('dependency_unavailable')
            observations = tuple(item.progress.observation.outcome for item in current.operations)
        prepared = self.preparer.prepare(principal, history.authoring, batch, observations)
        return DispatchPrerequisites(prepared.status, prepared)
