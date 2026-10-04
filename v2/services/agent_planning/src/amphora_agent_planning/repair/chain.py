"""Bounded iteration over explicitly published diagnostics; no hidden publisher."""

from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_planning import ExtractionTraceRef

from ..context.policy import require
from ..orchestration.runner import BUDGET_STOPS
from .history import RepairHistory
from .request import step_identity
from .runner import RepairInputUnavailable, RepairStep


@dataclass(frozen=True)
class RepairInputs:
    parent: ExtractionTraceRef
    feedback: ArtifactRef
    interpretation: ArtifactRef


@dataclass(frozen=True)
class RepairChainResult:
    steps: tuple[RepairStep, ...]
    stop_reason: str


class RepairChain:
    def __init__(self, runner, producer):
        self.runner, self.producer = runner, producer

    def run(self, principal, root, initial):
        history = RepairHistory.read(self.runner.engine, principal, root, initial.parent)
        maximum = history.root.task.request.document().context.limits.max_attempts
        inputs, seen, steps = initial, set(), []
        for ordinal in range(maximum):
            identity = step_identity(inputs.parent, inputs.feedback, inputs.interpretation)
            require(identity not in seen, "repair_chain_cycle")
            seen.add(identity)
            try:
                step = self.runner.execute(principal, root, inputs.parent, inputs.feedback, inputs.interpretation)
            except RepairInputUnavailable as exc:
                return RepairChainResult(tuple(steps), exc.reason)
            steps.append(step)
            if step.stop_reason in BUDGET_STOPS | {"attempt_pending", "abstained", "policy_rejected"}:
                return RepairChainResult(tuple(steps), step.stop_reason)
            require(step.trace is not None, "repair_chain_trace_missing")
            if ordinal + 1 == maximum:
                return RepairChainResult(tuple(steps), "repair_chain_limit")
            # Configured owner boundary, outside SQL. None means no further repair requested.
            try:
                following = self.producer.next(step)
            except RepairInputUnavailable as exc:
                return RepairChainResult(tuple(steps), exc.reason)
            if following is None:
                return RepairChainResult(tuple(steps), "repair_complete")
            require(isinstance(following, RepairInputs) and following.parent == step.trace.reference(),
                    "repair_chain_parent")
            inputs = following
        raise AssertionError("unreachable")
