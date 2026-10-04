"""Only a newly issued durable ticket permits this runner to invoke its adapter."""

from dataclasses import dataclass

from ..context import AttemptBinding
from ..context.policy import require
from ..persistence.budget import BudgetLedger
from ..persistence.dispatch import DispatchJournal
from ..persistence.journal import PlanningJournal
from ..persistence.records import AttemptJournal
from ..persistence.settlement import SettlementJournal
from ..providers import observe
from ..providers.capture import CapturedOutput, Observation, unknown_usage

BUDGET_STOPS = frozenset({"token_budget_exhausted", "accounting_budget_exhausted", "provider_usage_overage",
    "repair_attempt_budget_exhausted", "repair_token_budget_exhausted", "repair_accounting_budget_exhausted"})


@dataclass(frozen=True)
class RunOutcome:
    attempts: tuple[AttemptJournal, ...]
    stop_reason: str

    @property
    def latest(self):
        return self.attempts[-1] if self.attempts else None


class PlanningRunner:
    def __init__(self, engine, provider, *, timeout_seconds):
        require(type(timeout_seconds) is int and 1 <= timeout_seconds <= 86400, "dispatch_timeout")
        self.provider = provider
        self.timeout_seconds = timeout_seconds
        self.journal = PlanningJournal(engine)
        self.ledger = BudgetLedger(engine)
        self.dispatch = DispatchJournal(engine)
        self.settlements = SettlementJournal(engine)

    def execute(self, principal, binding, reviewed_policy):
        self.journal.register(principal, binding.request)
        self.ledger.reserve(principal, binding, reviewed_policy)
        ticket = self.dispatch.issue(principal, binding, self.timeout_seconds)
        if ticket is None:
            current = self.journal.read_attempt(principal, binding.reference())
            if current.observation is None:
                try:
                    current = self.dispatch.recover(principal, binding)
                except ValueError as exc:
                    if str(exc) != "attempt_not_expired":
                        raise
            if current.observation is not None:
                self.settlements.settle(principal, binding)
            return current
        # No database transaction is open here. A crash leaves issuance for deadline recovery.
        try:
            observed = observe(binding, self.provider)
        except Exception:
            # Adapter preflight/property failures are bounded, redacted unknown outcomes too.
            observed = Observation.record(binding, CapturedOutput(b"", False), "unknown", "adapter_failure",
                                          unknown_usage())
        current = self.dispatch.complete(principal, binding, ticket, observed)
        self.settlements.settle(principal, binding)
        return current

    def run(self, principal, snapshot, reviewed_policy):
        attempts = []
        for ordinal in range(1, snapshot.document().context.limits.max_attempts + 1):
            binding = AttemptBinding(snapshot, ordinal)
            try:
                current = self.execute(principal, binding, reviewed_policy)
            except ValueError as exc:
                if str(exc) not in BUDGET_STOPS:
                    raise
                return RunOutcome(tuple(attempts), str(exc))
            attempts.append(current)
            if current.observation is None:
                return RunOutcome(tuple(attempts), "attempt_pending")
            status = current.observation.document().status
            if status in {"proposed", "abstained", "policy_rejected"}:
                return RunOutcome(tuple(attempts), status)
        return RunOutcome(tuple(attempts), "attempt_limit")
