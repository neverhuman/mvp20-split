"""Graph-specific exchange policy; owned persistence has separate SQL tests."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_agent_planning.owner_handoff.events import HandoffEvent, HandoffProgress
from amphora_agent_planning.owner_handoff.exchange import OwnerExchange
from amphora_agent_planning.owner_handoff.journal import HandoffState
from amphora_agent_planning.owner_handoff.policy import SubmissionPolicy
from amphora_agent_planning.owner_handoff.transport import (
    HandoffWindow,
    OwnerAbsent,
    OwnerUnavailable,
)

from .test_values import accepted_fixture


class Journal:
    def __init__(self, request, position):
        self.state = HandoffState(request.selection, SimpleNamespace(request=request), HandoffProgress("prepared"), position, None, ())
        self.store = SimpleNamespace(guard=lambda *_args: None)

    def advance(self, principal, lease, position, action, data):
        assert position == self.state.position
        event = HandoffEvent.record(self.state.payload.request, position + 1, action, data)
        progress = event.apply(self.state.progress, self.state.payload.request, position + 1)
        self.state = replace(self.state, progress=progress, position=position + 1,
            events=self.state.events + ((event, None),))
        return self.state


class GraphPeer:
    def __init__(self, status, accepted, initial):
        self.status, self.accepted_record, self.initial = status, accepted, initial
        self.writes = self.reads = self.accepted_reads = 0
        self.accepted_fault = None

    def read(self, request, window, guard):
        window.start()
        guard()
        self.reads += 1
        if self.writes or self.initial == "accepted":
            return self.status
        if self.initial == "pending":
            return self.status.model_copy(update={"decision": None})
        raise OwnerAbsent("absent")

    def submit(self, request, window, guard):
        window.start()
        guard()
        self.writes += 1
        return self.status.decision

    def accepted(self, request, reference, window, guard):
        window.start()
        guard()
        self.accepted_reads += 1
        assert reference == self.accepted_record.reference
        if self.accepted_fault:
            raise self.accepted_fault
        return self.accepted_record


def exchange(initial, position=1):
    request, status, accepted = accepted_fixture()
    journal = Journal(request, position)
    peer = GraphPeer(status, accepted, initial)
    return OwnerExchange(journal, None, None, peer, HandoffWindow(), journal.state), peer


@pytest.mark.parametrize("initial", ["absent", "pending"])
def test_graph_submit_requires_exact_status_and_accepted_readback(initial):
    step, peer = exchange(initial)
    assert step.read() is True
    assert SubmissionPolicy.block(step.state) is None
    step.submit()
    assert step.state.terminal and step.state.progress.state == "acknowledged"
    assert (peer.reads, peer.writes, peer.accepted_reads, step.window.calls) == (2, 1, 1, 4)
    assert step.state.progress.outcome.state == "acknowledged"


def test_existing_acceptance_resolves_without_post_even_at_last_slot():
    step, peer = exchange("accepted", position=63)
    assert step.read() is False
    assert step.state.terminal and step.state.position == 64
    assert (peer.writes, peer.accepted_reads) == (0, 1)


def test_missing_accepted_readback_never_turns_decision_into_acknowledgment():
    step, peer = exchange("accepted")
    peer.accepted_fault = OwnerUnavailable("temporary")
    assert step.read() is False
    assert not step.state.terminal and step.reason == "owner_unavailable"
    assert step.state.progress.outcome.state == "awaiting_accepted_readback"
    assert peer.writes == 0


def test_capacity_blocks_new_submission_but_keeps_pending_evidence():
    step, peer = exchange("pending", position=63)
    assert step.read() is True
    assert SubmissionPolicy.block(step.state) == "event_limit"
    assert step.state.position == 63 and peer.writes == 0


def test_mismatched_post_receipt_is_not_accepted():
    step, peer = exchange("absent")
    assert step.read()
    peer.status = peer.status.model_copy(update={"decision": peer.status.decision.model_copy(update={"request_sha256": "0" * 64})})
    step.submit()
    assert not step.state.terminal and step.reason == "identity_conflict"


@pytest.mark.parametrize("outcome", ["rejected", "conflict"])
def test_negative_owner_decision_is_terminal_without_new_submission(outcome):
    from amphora_contracts_core import Finding
    from amphora_contracts_knowledge import FailedDecision
    step, peer = exchange("accepted")
    decision = peer.status.decision.model_copy(update={"decision": FailedDecision(outcome=outcome,
        findings=(Finding(code="stale_head", location="proposal", message="Future campaign may revise"),))})
    peer.status = peer.status.model_copy(update={"decision": decision})
    assert step.read() is False and step.state.progress.state == outcome
    assert step.state.terminal and peer.writes == peer.accepted_reads == 0
