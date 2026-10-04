"""Result journal plus actual SDK; public Data/preparation peers are scripted."""

import pytest
from amphora_agent_planning.result_publication.history import ResultHistory
from amphora_agent_planning.result_publication.prepared import PreparedResult
from amphora_agent_planning.result_publication.workflow import (
    ResultInputs,
    ResultPublisher,
)
from amphora_tool_protocol import ArtifactClient, Reply, TransportLost, WorkerIdentity
from sqlalchemy import event

from ..publication.test_workflow import DataPeer
from .test_journal import setup_result

pytestmark = pytest.mark.postgres


class Preparer:
    def __init__(self, review, feedback):
        self.review, self.feedback, self.calls = review, feedback, 0

    def prepare(self, history, selection):
        assert history.task == self.review.task and history.projection.reference() == selection.trace()
        self.calls += 1
        return ResultInputs(self.review, feedback=self.feedback)


def workflow(stored):
    store, journal, selection, review, feedback = setup_result(stored)
    with stored.engine.begin() as connection:
        history = ResultHistory.load(connection, stored.principal, selection, store.traces)
    prepared = PreparedResult.create(stored.principal, selection, history, review, feedback=feedback)
    peer = DataPeer(prepared.identity, prepared.artifact)
    preparer = Preparer(review, feedback)
    publisher = ResultPublisher(journal, preparer, ArtifactClient(peer, WorkerIdentity(stored.principal.actor_id, stored.principal.scope)))
    return publisher, peer, preparer, selection


def test_result_sdk_reconciles_begin_and_terminal_replay_needs_no_input_reads(stored):
    publisher, peer, preparer, selected = workflow(stored)
    peer.lost_begin = True
    state = publisher.publish(stored.principal, selected)
    assert state.attempt.stage == "finalized" and state.position == 6
    assert len(peer.uploads) == 1 and preparer.calls == 1
    assert [method for method, _, _ in peer.calls].count("PUT") == 1
    calls = list(peer.calls)
    assert publisher.publish(stored.principal, selected) == state
    assert peer.calls == calls and preparer.calls == 1


def test_result_uncertain_put_uses_distinct_successor_never_repeats_old_put(stored):
    publisher, peer, preparer, selected = workflow(stored)
    peer.lost_put = True
    with pytest.raises(TransportLost):
        publisher.publish(stored.principal, selected)
    first = publisher.journal.read(stored.principal, selected.publication_id)
    assert first.attempt.stage == "streaming"
    peer.lost_put = False
    final = publisher.publish(stored.principal, selected)
    assert final.attempt.stage == "finalized" and final.attempt.identity.ordinal == 2
    puts = [path for method, path, _ in peer.calls if method == "PUT"]
    assert len(puts) == len(set(puts)) == 2 and preparer.calls == 1
    assert final.events[:len(first.events)] == first.events


@pytest.mark.parametrize("fault", ["finalize", "derivation", "forged"])
def test_result_uncertain_finalize_keeps_original_command_without_restream(stored, fault):
    publisher, peer, preparer, selected = workflow(stored)
    peer.lost_finalize, peer.derivation_down, peer.forge = fault == "finalize", fault == "derivation", fault == "forged"
    with pytest.raises(ValueError):
        publisher.publish(stored.principal, selected)
    retained = publisher.journal.read(stored.principal, selected.publication_id)
    assert retained.attempt.stage == "finalizing"
    peer.lost_finalize = peer.final_lookup_down = peer.derivation_down = peer.forge = False
    final = publisher.publish(stored.principal, selected)
    assert final.attempt.identity == retained.attempt.identity and final.attempt.stage == "finalized"
    assert [method for method, _, _ in peer.calls].count("PUT") == 1 and preparer.calls == 1


@pytest.mark.parametrize("stage", ["begin", "finalize"])
def test_result_rejection_is_terminal_even_after_peer_policy_changes(stored, stage):
    publisher, peer, preparer, selected = workflow(stored)
    if stage == "begin": peer.reject = True
    else: peer.after_put = lambda: setattr(peer, "reject", True)
    rejected = publisher.publish(stored.principal, selected)
    assert rejected.attempt.rejection == "source_process_denied"
    count = len(peer.calls)
    peer.reject = False
    assert publisher.publish(stored.principal, selected) == rejected
    assert len(peer.calls) == count and preparer.calls == 1


@pytest.mark.parametrize("fault", ["identity", "input_denial", "input_contract"])
def test_wrong_client_or_unavailable_preparation_never_emits_remote_effect(stored, fault):
    publisher, peer, preparer, selected = workflow(stored)
    if fault == "identity": publisher.client.identity = WorkerIdentity("foreign", stored.principal.scope)
    if fault == "input_denial":
        def denied(*_): raise ValueError("source_access_denied")
        preparer.prepare = denied
    if fault == "input_contract": preparer.prepare = lambda *_: {"accepted": True}
    with pytest.raises(ValueError):
        publisher.publish(stored.principal, selected)
    assert not peer.calls
    assert publisher.journal.read(stored.principal, selected.publication_id).payload is None
    lease = publisher.journal.store.acquire(stored.principal, selected.publication_id)
    publisher.journal.store.release(stored.principal, lease)


def test_result_input_and_peer_calls_run_outside_sql_transactions(stored):
    publisher, peer, preparer, selected = workflow(stored)
    active = set()
    def begin(connection): active.add(id(connection))
    def end(connection): active.discard(id(connection))
    original_prepare, original_request = preparer.prepare, peer.request
    def prepare(*args):
        assert not active
        return original_prepare(*args)
    def request(*args, **kwargs):
        assert not active
        return original_request(*args, **kwargs)
    preparer.prepare, peer.request = prepare, request
    for name, callback in [("begin", begin), ("commit", end), ("rollback", end)]:
        event.listen(stored.engine, name, callback)
    try:
        assert publisher.publish(stored.principal, selected).attempt.stage == "finalized"
        assert not active
    finally:
        for name, callback in [("begin", begin), ("commit", end), ("rollback", end)]:
            event.remove(stored.engine, name, callback)


def test_result_lease_loss_after_remote_put_keeps_uncertain_streaming(stored):
    publisher, peer, _preparer, selected = workflow(stored)
    store = publisher.journal.store
    acquire, leases = store.acquire, []
    def captured(*args, **kwargs):
        lease = acquire(*args, **kwargs)
        leases.append(lease)
        return lease
    store.acquire = captured
    peer.after_put = lambda: store.release(stored.principal, leases[-1])
    with pytest.raises(ValueError, match="result_lease_lost"):
        publisher.publish(stored.principal, selected)
    assert publisher.journal.read(stored.principal, selected.publication_id).attempt.stage == "streaming"
    assert not any(path.endswith("/finalize") for _, path, _ in peer.calls)
    peer.after_put = lambda: None
    assert publisher.publish(stored.principal, selected).attempt.identity.ordinal == 2


@pytest.mark.parametrize("status", [403, 503])
def test_result_receipt_lookup_failure_never_blindly_resubmits(stored, status):
    publisher, peer, _preparer, selected = workflow(stored)
    calls = []
    def unavailable(method, path, body=None, **kwargs):
        calls.append((method, path))
        return Reply(status, b"")
    peer.request = unavailable
    with pytest.raises(ValueError):
        publisher.publish(stored.principal, selected)
    assert all(method == "GET" for method, _ in calls) and 1 <= len(calls) <= 3
    assert publisher.journal.read(stored.principal, selected.publication_id).attempt.stage == "prepared"


@pytest.mark.parametrize("boundary", ["prepared", "begun", "streaming", "streamed", "finalizing", "finalized"])
def test_result_exception_after_commit_resumes_exact_history(stored, boundary):
    publisher, peer, preparer, selected = workflow(stored)
    journal = publisher.journal
    original_prepare, original_advance = journal.prepare, journal.advance
    def interrupt(state):
        if state.attempt.stage == boundary:
            raise RuntimeError("after_committed_transition")
        return state
    journal.prepare = lambda *args, **kwargs: interrupt(original_prepare(*args, **kwargs))
    journal.advance = lambda *args, **kwargs: interrupt(original_advance(*args, **kwargs))
    with pytest.raises(RuntimeError, match="after_committed_transition"):
        publisher.publish(stored.principal, selected)
    retained = journal.read(stored.principal, selected.publication_id)
    assert retained.attempt.stage == boundary
    journal.prepare, journal.advance = original_prepare, original_advance
    final = publisher.publish(stored.principal, selected)
    assert final.attempt.stage == "finalized" and final.events[:len(retained.events)] == retained.events
    puts = [path for method, path, _ in peer.calls if method == "PUT"]
    assert len(puts) == len(set(puts)) == 1 and preparer.calls == 1
    assert final.attempt.identity.ordinal == (2 if boundary == "streaming" else 1)


def test_unexpected_release_failure_is_not_hidden_by_completed_upload(stored):
    publisher, _peer, _preparer, selected = workflow(stored)
    def broken_release(*_): raise ValueError("unexpected_result_release_failure")
    publisher.journal.store.release = broken_release
    with pytest.raises(ValueError, match="unexpected_result_release_failure"):
        publisher.publish(stored.principal, selected)
    assert publisher.journal.read(stored.principal, selected.publication_id).attempt.stage == "finalized"
