"""Accepted report effects, separate from wire DTOs and SQL write sets."""

from dataclasses import dataclass

from ..lifecycle.claims import lease_from
from ..lifecycle.model import ActivationState, RunBudget, RunState


@dataclass(frozen=True, slots=True)
class CompletionDecision:
    activation: ActivationState
    lease: object
    budget: RunBudget

    @classmethod
    def evaluate(cls, proposal, run, row, worker, now):
        activation = ActivationState(row["activation_status"], row["current_fence"], row["attempt_count"],
            run["input_snapshot"]["budget"]["max_attempts_per_activation"], row["specification"].get("side_effects", "pure"))
        outcome = proposal.request.completion.outcome
        disposition = "uncertain" if outcome.status == "uncertain_external_effect" else outcome.status
        activation, lease, budget = activation.terminal(lease_from(row),
            RunBudget(run["budget_limit"], run["reserved"], run["spent"]), disposition,
            now=now, run=RunState(run["status"], run["revision"]),
            retryable=getattr(outcome, "retryable", False), authority=worker)
        return cls(activation, lease, budget)

    @property
    def canonical_result(self):
        return self.activation.status in {"succeeded", "abstained", "failed"}

    @staticmethod
    def run_status(statuses, *, execution_mode="fixture"):
        if "uncertain" in statuses:
            return "blocked"
        if execution_mode == "graph":
            # Only the graph coordinator may conclude a graph from its Finish/frontier.
            return "running"
        if any(s in {"queued", "leased"} for s in statuses):
            return "running"
        return "failed" if any(s in {"failed", "cancelled"} for s in statuses) else "completed"
