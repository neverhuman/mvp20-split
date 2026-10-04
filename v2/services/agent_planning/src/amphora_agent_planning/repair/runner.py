"""One immutable repair child, one physical attempt, and history-first recovery."""

import hashlib
import re
from dataclasses import dataclass

from ..context import AttemptBinding
from ..context.policy import require
from ..extraction import TraceProjection
from ..orchestration.runner import BUDGET_STOPS, PlanningRunner
from ..persistence.dispatch import DispatchJournal
from ..persistence.extraction import ExtractionJournal
from ..persistence.journal import PlanningJournal
from ..persistence.preparation import PreparationJournal
from ..persistence.records import AttemptJournal
from ..persistence.repair import RepairJournal
from ..persistence.settlement import SettlementJournal
from .history import RepairHistory
from .request import step_identity


@dataclass(frozen=True)
class RepairStep:
    attempt: AttemptJournal | None
    trace: TraceProjection | None
    stop_reason: str


class RepairInputUnavailable(ValueError):
    """A required input could not be freshly verified; retain preceding steps."""

    def __init__(self, reason):
        self.reason = reason if re.fullmatch(r"[a-z][a-z0-9_]{0,127}", reason) else "repair_input_unavailable"
        super().__init__(self.reason)


class PacketProvider:
    """Private configured adapter port: reply(binding, packet), never refs alone."""

    def __init__(self, provider, prepared, stored):
        document = stored.manifest.document()
        require(document.request_sha256 == prepared.plan.task.request.sha256 and
                document.packet.sha256 == hashlib.sha256(prepared.packet).hexdigest() and
                document.packet.size_bytes == len(prepared.packet), "repair_adapter_packet")
        self.provider, self.packet = provider, prepared.packet
        self.request_sha256 = document.request_sha256

    def supports(self, model):
        return self.provider.supports(model)

    def reply(self, binding):
        require(binding.request.sha256 == self.request_sha256 and binding.ordinal == 1, "repair_adapter_request")
        return self.provider.reply(binding, self.packet)


class RepairRunner:
    def __init__(self, engine, preparer, provider, *, timeout_seconds):
        require(type(timeout_seconds) is int and 1 <= timeout_seconds <= 86400, "dispatch_timeout")
        self.engine, self.preparer, self.provider = engine, preparer, provider
        self.timeout_seconds = timeout_seconds
        self.journal, self.traces = PlanningJournal(engine), ExtractionJournal(engine)
        self.families, self.preparations = RepairJournal(engine), PreparationJournal(engine)

    def _result(self, principal, task, attempt, parent, identity):
        if attempt.observation is None:
            return RepairStep(attempt, None, "attempt_pending")
        SettlementJournal(self.engine).settle(principal, attempt.binding)
        trace = self.traces.record(principal, task.document().task_id, attempt.binding.reference(),
                                   "repair-trace-" + identity, parent).projection
        return RepairStep(attempt, trace, attempt.observation.document().status)

    def _execute(self, principal, root, parent, feedback, interpretation):
        history = RepairHistory.read(self.engine, principal, root, parent)
        identity = step_identity(parent, feedback, interpretation)
        task = self.traces.read_task(principal, "repair-task-" + identity)
        if task is not None:
            task = task.snapshot
            member = self.families.read(principal, task.document().engagement)
            if member is not None:
                require(member.root.canonical == history.root.canonical, "repair_parent_membership")
            binding = AttemptBinding(task.request, 1)
            current = self.journal.read_attempt(principal, binding.reference())
            if current is not None and (current.observation is not None or self.preparations.issued(principal, binding)):
                prepared = self.preparations.read(principal, task.document().engagement)
                require(prepared is not None and prepared.manifest.document().parent == parent, "repair_preparation_unknown")
                if current.observation is None:
                    try:
                        current = DispatchJournal(self.engine).recover(principal, binding)
                    except ValueError as exc:
                        if str(exc) != "attempt_not_expired":
                            raise
                return self._result(principal, task, current, parent, identity)
        status = history.observation.document().status
        if status in {"abstained", "policy_rejected"}:
            return RepairStep(None, None, status)
        # No SQL transaction encloses peer reads or provider calls.
        try:
            prepared = self.preparer.prepare(history, feedback, interpretation)
        except (ValueError, PermissionError) as exc:
            raise RepairInputUnavailable(str(exc)) from exc
        task = prepared.plan.task
        self.journal.register(principal, task.request)
        self.traces.register(principal, task)
        self.families.enroll_child(principal, root, task.document().task_id, parent)
        stored = self.preparations.register(principal, prepared)
        provider = PacketProvider(self.provider, prepared, stored)
        try:
            attempt = PlanningRunner(self.engine, provider, timeout_seconds=self.timeout_seconds).execute(
                principal, AttemptBinding(task.request, 1), history.root.policy)
        except ValueError as exc:
            if str(exc) not in BUDGET_STOPS:
                raise
            return RepairStep(None, None, str(exc))
        return self._result(principal, task, attempt, parent, identity)

    def execute(self, principal, root, parent, feedback, interpretation):
        for retry in range(3):
            try:
                return self._execute(principal, root, parent, feedback, interpretation)
            except ValueError as exc:
                if str(exc) != "repair_membership_changed" or retry == 2:
                    raise
        raise AssertionError("unreachable")
