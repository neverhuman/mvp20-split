"""Real Planning state and scripted peer outcomes; no actual owner acceptance."""

import pytest
from amphora_agent_planning.owner_handoff.preparation import HandoffInputs
from amphora_agent_planning.owner_handoff.transport import (
    OwnerAbsent,
    OwnerDenied,
    OwnerInvalid,
    OwnerUnavailable,
)
from amphora_agent_planning.owner_handoff.workflow import OwnerHandoff

from .test_journal import setup_handoff

pytestmark = pytest.mark.postgres


class Preparer:
    def __init__(self, engine, review, questions):
        self.engine, self.review, self.questions = engine, review, questions
        self.preparations = self.authorizations = 0
        self.denied = False

    def prepare(self, history, selection):
        assert self.engine.pool.checkedout() == 0
        self.preparations += 1
        return HandoffInputs(self.review, self.questions)

    def authorize(self, history, payload, *, seconds):
        assert self.engine.pool.checkedout() == 0 and 0 < seconds <= 20
        self.authorizations += 1
        if self.denied:
            raise ValueError("source_access_denied")


class Peer:
    owner_id, owner = "research", "research"

    def __init__(self, engine):
        self.engine, self.record = engine, None
        self.reads = self.writes = 0
        self.read_fault = self.write_fault = None
        self.lose_reply = False

    def read(self, request, window, guard=None):
        assert self.engine.pool.checkedout() == 0
        guard()
        window.start()
        self.reads += 1
        if self.read_fault is not None:
            raise self.read_fault
        if self.record is None:
            raise OwnerAbsent("handoff_absent")
        return self.record

    def submit(self, request, window, guard=None):
        assert self.engine.pool.checkedout() == 0
        guard()
        window.start()
        self.writes += 1
        if self.write_fault is not None:
            raise self.write_fault
        self.record = request.document()
        if self.lose_reply:
            self.lose_reply = False
            raise OwnerUnavailable("handoff_write_uncertain")
        return self.record


def workflow(stored):
    _store, journal, selection, review, questions = setup_handoff(stored)
    preparer, peer = Preparer(stored.engine, review, questions), Peer(stored.engine)
    return OwnerHandoff(journal, preparer, peer), selection, preparer, peer


def test_first_submit_is_read_first_and_terminal_replay_has_no_effects(stored):
    owner, selection, preparer, peer = workflow(stored)
    result = owner.submit(stored.principal, selection)
    assert result.state.terminal and result.reason is None
    assert (preparer.preparations, preparer.authorizations, peer.reads, peer.writes) == (1, 1, 1, 1)
    preparer.denied = True
    peer.read_fault = AssertionError("terminal replay cannot contact owner")
    assert owner.submit(stored.principal, selection) == result
    assert (preparer.preparations, preparer.authorizations, peer.reads, peer.writes) == (1, 1, 1, 1)


def test_lost_write_reconciles_existing_record_without_new_processing(stored):
    owner, selection, preparer, peer = workflow(stored)
    peer.lose_reply = True
    first = owner.submit(stored.principal, selection)
    assert first.state.progress.state == "uncertain" and peer.writes == 1
    preparer.denied = True
    recovered = owner.submit(stored.principal, selection)
    assert recovered.state.terminal and recovered.state.payload == first.state.payload
    assert recovered.state.prepared_at == first.state.prepared_at
    assert preparer.authorizations == peer.writes == 1 and peer.reads == 2


def test_rights_withdrawal_after_preparation_prevents_new_post(stored):
    owner, selection, preparer, peer = workflow(stored)
    preparer.denied = True
    first = owner.submit(stored.principal, selection)
    assert first.reason == "source_access_denied" and peer.writes == 0
    preparer.denied = False
    result = owner.submit(stored.principal, selection)
    assert result.state.terminal and result.state.payload == first.state.payload
    assert preparer.preparations == 1 and preparer.authorizations == 2 and peer.writes == 1


@pytest.mark.parametrize("fault,reason", [(OwnerDenied("denied"), "owner_access_denied"),
    (OwnerUnavailable("uncertain"), "owner_unavailable"), (ValueError("hostile body"), "owner_protocol")])
def test_denied_or_ambiguous_read_never_authorizes_write(stored, fault, reason):
    owner, selection, preparer, peer = workflow(stored)
    peer.read_fault = fault
    result = owner.submit(stored.principal, selection)
    assert result.reason == reason and not result.state.terminal
    assert preparer.authorizations == peer.writes == 0


def test_explicit_write_rejection_survives_later_temporary_failure(stored):
    owner, selection, preparer, peer = workflow(stored)
    peer.write_fault = OwnerInvalid("invalid")
    first = owner.submit(stored.principal, selection)
    assert first.reason == "request_rejected" and peer.writes == 1
    peer.read_fault = OwnerUnavailable("temporary")
    assert owner.submit(stored.principal, selection).reason == "owner_unavailable"
    peer.read_fault = peer.write_fault = None
    assert owner.submit(stored.principal, selection).reason == "request_rejected"
    assert preparer.authorizations == peer.writes == 1


def test_lease_loss_after_rights_review_prevents_dispatch(stored, monkeypatch):
    owner, selection, preparer, peer = workflow(stored)
    store = owner.journal.store
    acquired = []
    original = store.acquire
    def acquire(*args, **kwargs):
        lease = original(*args, **kwargs)
        acquired.append(lease)
        return lease
    monkeypatch.setattr(store, "acquire", acquire)
    def authorize(*args, **kwargs):
        store.release(stored.principal, acquired[0])
    preparer.authorize = authorize
    with pytest.raises(ValueError, match="handoff_lease_lost"):
        owner.submit(stored.principal, selection)
    assert peer.reads == 1 and peer.writes == 0


def test_completion_between_initial_read_and_acquire_is_historical_replay(stored, monkeypatch):
    owner, selection, preparer, peer = workflow(stored)
    preparer.denied = True
    previous = owner.submit(stored.principal, selection).state
    preparer.denied = False
    completed = owner.submit(stored.principal, selection)
    original = owner.journal.read
    snapshots = [previous]
    def read(*args):
        return snapshots.pop() if snapshots else original(*args)
    monkeypatch.setattr(owner.journal, "read", read)
    peer.read_fault = AssertionError("terminal owner was contacted")
    assert owner.submit(stored.principal, selection) == completed


def test_source_preparation_gap_retains_only_unprepared_slot(stored):
    owner, selection, preparer, peer = workflow(stored)
    def unavailable(*args):
        raise ValueError("source_reference_unavailable")
    preparer.prepare = unavailable
    result = owner.submit(stored.principal, selection)
    assert result.state.payload is None and result.state.position == 0
    assert result.reason == "source_unavailable" and peer.reads == peer.writes == 0


def test_unknown_local_candidate_never_becomes_an_arbitrary_owner_request(stored):
    from amphora_agent_planning.owner_handoff.selection import HandoffSelection
    owner, selection, _, peer = workflow(stored)
    unknown = HandoffSelection.bind(stored.principal, selection.trace(), "publication", "question", "unknown", "research")
    result = owner.submit(stored.principal, unknown)
    assert result.reason == "candidate_unavailable" and result.state.payload is None
    assert peer.reads == peer.writes == 0
