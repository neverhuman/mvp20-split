"""Durable per-effect handoff with read-first recovery and fresh write permission."""

from dataclasses import dataclass

from ..context.policy import require
from .exchange import OwnerExchange
from .history import HandoffHistory
from .journal import HandoffState
from .policy import SubmissionPolicy
from .preparation import HandoffInputs
from .transport import HandoffWindow


@dataclass(frozen=True)
class HandoffResult:
    state: HandoffState
    reason: str | None = None


def input_reason(error):
    code = str(error)
    if code.startswith(("handoff_lease", "stored_")) or code in {"handoff_payload_conflict", "handoff_position_conflict"}:
        raise error
    if code == "source_access_denied":
        return "source_access_denied"
    if code in {"handoff_graph_context_missing", "handoff_question_context_missing", "handoff_dependency_unacknowledged"}:
        return "dependency_unavailable"
    if code == "handoff_candidate_unavailable":
        return "candidate_unavailable"
    return "source_unavailable"


class OwnerHandoff:
    def __init__(self, journal, preparer, transport):
        require(journal.store.owner_id == transport.owner_id, "handoff_configuration_conflict")
        self.journal, self.preparer, self.transport = journal, preparer, transport

    def submit(self, principal, selection):
        owner = "knowledge" if selection.document()["kind"] == "graph" else "research"
        require(owner == self.transport.owner, "handoff_owner_binding")
        store = self.journal.store
        selected = store.register(principal, selection)
        state = self.journal.read(principal, selected.effect_id)
        if state.terminal:
            return HandoffResult(state)
        lease = store.acquire(principal, selected.effect_id, seconds=120)
        try:
            state = self.journal.read(principal, selected.effect_id)
            if state.terminal:
                return HandoffResult(state)
            with store.engine.begin() as connection:
                history = HandoffHistory.load(connection, principal, selected, store.traces)
            if state.payload is None:
                try:
                    inputs = self.preparer.prepare(history, selected)
                    require(isinstance(inputs, HandoffInputs), "handoff_preparer_contract")
                    state = self.journal.prepare(principal, lease, inputs.sources,
                        questions=inputs.questions, knowledge=inputs.knowledge)
                except ValueError as error:
                    return HandoffResult(state, input_reason(error))
            exchange = OwnerExchange(self.journal, principal, lease, self.transport, HandoffWindow(), state)
            if exchange.read():
                reason = SubmissionPolicy.block(exchange.state)
                if reason is not None:
                    return HandoffResult(exchange.state, reason)
                try:
                    self.preparer.authorize(history, exchange.state.payload, seconds=exchange.window.remaining())
                except ValueError as error:
                    reason = input_reason(error)
                    exchange.block(reason)
                else:
                    exchange.submit()
            return HandoffResult(exchange.state, exchange.reason)
        finally:
            try:
                store.release(principal, lease)
            except ValueError as error:
                if str(error) != "handoff_lease_lost":
                    raise
