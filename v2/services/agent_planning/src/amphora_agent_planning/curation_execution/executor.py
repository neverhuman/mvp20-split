"""Original issuance token controls one physical call; replacement only recovers."""
from datetime import datetime, timezone
from ..context import AttemptBinding
from ..context.policy import require
from ..curation_declaration.journal import DeclarationJournal
from ..curation_jobs.journal import CurationJobs, key_for
from ..curation_preparation.link import CurationPreparationJournal
from ..persistence.budget import BudgetLedger
from ..persistence.dispatch import DispatchJournal
from ..persistence.journal import PlanningJournal
from ..persistence.settlement import SettlementJournal
from ..providers import observe
from ..providers.capture import Observation, CapturedOutput, unknown_usage
from .packet import authorize, CurationProvider


class CurationExecutor:
    def __init__(self, engine, data, provider, *, timeout_seconds=60):
        require(type(timeout_seconds) is int and 1 <= timeout_seconds <= 60, 'curation_execution_timeout')
        self.engine, self.data, self.provider, self.timeout = engine, data, provider, timeout_seconds
        self.jobs, self.inputs = CurationJobs(engine), CurationPreparationJournal(engine)
        self.declarations, self.attempts = DeclarationJournal(engine), PlanningJournal(engine)
        self.budgets, self.dispatch, self.settlements = BudgetLedger(engine), DispatchJournal(engine), SettlementJournal(engine)

    def _guard(self, principal, lease, conn):
        progress, _ = self.jobs._owned(conn, principal, lease, key_for(principal, lease.curation_id))
        require(progress.view.receipt.phase == 'awaiting_provider', 'curation_execution_phase')

    def _check(self, principal, lease):
        with self.engine.begin() as conn:
            self._guard(principal, lease, conn)

    def execute(self, principal, lease):
        principal.require('execute_curations', principal.scope)
        recovered = self.inputs.recover(principal, lease.curation_id)
        require(recovered is not None and recovered.link is not None, 'curation_execution_input')
        frozen = recovered.link.frozen
        binding = AttemptBinding(frozen.preparation.packet.request, 1)
        current = self.attempts.read_attempt(principal, binding.reference())
        if current is not None and current.observation is not None:
            self.settlements.settle(principal, binding)
            return current
        key = {**self.attempts._key(binding.reference().engagement), 'ordinal': 1}
        with self.engine.connect() as conn:
            issued = self.dispatch._issued(conn, key)
        if issued is not None:
            try:
                current = self.dispatch.recover(principal, binding)
            except ValueError as error:
                if str(error) != 'attempt_not_expired': raise
                return self.attempts.read_attempt(principal, binding.reference())
            self.settlements.settle(principal, binding)
            return current
        # Only unissued work needs current configuration/processing and a job fence.
        self._check(principal, lease)
        declaration = self.declarations.read(principal, lease.curation_id)
        require(declaration is not None and declaration.attempt.stage == 'finalized', 'curation_execution_declaration')
        reviewed = declaration.identity.reviewed()
        intent = reviewed.with_artifact(declaration.attempt.result.artifact)
        require(intent.request == binding.request, 'curation_execution_original_declaration')
        require(self.provider is not None, 'curation_provider_unconfigured')
        self.provider.validate_policy(reviewed.budget)
        authorize(frozen, self.data)
        guard = lambda conn: self._guard(principal, lease, conn)
        self.budgets.reserve(principal, binding, reviewed.budget, guard=guard)
        ticket = self.dispatch.issue(principal, binding, self.timeout, guard=guard)
        if ticket is None:
            return self.attempts.read_attempt(principal, binding.reference())
        def before_send():
            self._check(principal, lease)
            authorize(frozen, self.data)
            self._check(principal, lease)
        delta = ticket.deadline - datetime(1970, 1, 1, tzinfo=timezone.utc)
        deadline = delta.days * 86400000 + delta.seconds * 1000 + delta.microseconds // 1000
        try:
            observed = observe(binding, CurationProvider(self.provider, frozen, before_send, deadline))
        except Exception:
            observed = Observation.record(binding, CapturedOutput(b"", False), "unknown",
                "adapter_failure", unknown_usage())
        result = self.dispatch.complete(principal, binding, ticket, observed)
        self.settlements.settle(principal, binding)
        return result
