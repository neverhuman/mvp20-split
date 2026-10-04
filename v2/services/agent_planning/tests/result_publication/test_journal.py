"""Actual owner storage/fences; Data receipts remain scripted here."""

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_agent_planning.repair.feedback import RepairFeedback
from amphora_agent_planning.result_publication.history import ResultHistory
from amphora_agent_planning.result_publication.journal import ResultJournal
from amphora_agent_planning.result_publication.selection import ResultSelection
from amphora_agent_planning.result_publication.store import ResultStore
from amphora_contracts_core import Finding
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from ..publication.test_values import receipts
from .test_history import finalize

pytestmark = pytest.mark.postgres


def setup_result(stored):
    traces, selection, review = finalize(stored)
    with stored.engine.begin() as connection:
        history = ResultHistory.load(connection, stored.principal, selection, traces)
    feedback = RepairFeedback.create(history.task, history.projection, history.observation,
        (Finding(code="unresolved", location="/assertions/0", message="Keep useful output"),))
    store = ResultStore(stored.engine, "data-owner", trace_publisher_id="data-owner")
    assert store.register(stored.principal, selection) == selection
    return store, ResultJournal(store), selection, review, feedback


def test_result_preparation_finalization_and_replacement_preserve_exact_history(stored):
    store, journal, selected, review, feedback = setup_result(stored)
    principal, key = stored.principal, selected.publication_id
    assert store.register(principal, selected) == selected
    assert journal.read(principal, key).identity is None
    assert journal.read(principal, "unknown") is None
    lease = store.acquire(principal, key)
    state = journal.prepare(principal, lease, review, feedback=feedback)
    assert journal.prepare(principal, lease, review, feedback=feedback) == state
    assert state.payload.artifact.body == feedback.canonical and state.payload.questions == b"null"
    first_time = state.prepared_at
    upload, stream, receipt, derivation = receipts(state.identity, state.payload.artifact, state.attempt)
    for action, value in [("begun", upload.model_dump(mode="json")), ("streaming", None),
        ("streamed", stream.model_dump(mode="json")), ("finalizing", None),
        ("finalized", {"receipt": receipt.model_dump(mode="json"), "derivation": derivation.model_dump(mode="json")})]:
        state = journal.advance(principal, lease, state.position, action, value)
    store.release(principal, lease)
    assert state.prepared_at == first_time and state.position == 6
    engine = create_engine(stored.engine.url)
    try:
        replacement = ResultJournal(ResultStore(engine, "data-owner", trace_publisher_id="data-owner"))
        reader = replace(principal, actions=frozenset({"read_attempts"}))
        assert replacement.read(reader, key) == state
    finally:
        engine.dispose()


def test_changed_payload_selection_or_configuration_cannot_create_new_effect(stored):
    store, journal, selected, review, feedback = setup_result(stored)
    lease = store.acquire(stored.principal, selected.publication_id)
    first = journal.prepare(stored.principal, lease, review, feedback=feedback)
    from amphora_agent_planning.publication.records import encode
    raw = feedback.document().model_dump(mode="json")
    raw["findings"][0]["message"] = "Changed findings"
    changed = RepairFeedback.from_bytes(encode(raw))
    with pytest.raises(ValueError, match="result_payload_conflict"):
        journal.prepare(stored.principal, lease, review, feedback=changed)
    alternate = ResultSelection.bind(stored.principal, selected.trace(), "another-interpretation", "feedback", "diagnostics", "data-owner")
    assert alternate.publication_id == selected.publication_id
    with pytest.raises(ValueError, match="result_selection_conflict"):
        store.register(stored.principal, alternate)
    wrong_config = ResultStore(stored.engine, "changed", trace_publisher_id="data-owner")
    with pytest.raises(ValueError, match="result_configuration_conflict"):
        ResultJournal(wrong_config).read(stored.principal, selected.publication_id)
    assert journal.read(stored.principal, selected.publication_id) == first


def test_two_lease_holders_and_stream_intents_have_one_winner(stored):
    store, journal, selected, review, feedback = setup_result(stored)
    barrier = Barrier(2)
    def acquire(_):
        barrier.wait(timeout=5)
        try:
            return store.acquire(stored.principal, selected.publication_id)
        except ValueError as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(acquire, range(2)))
    assert outcomes.count("result_lease_unavailable") == 1
    lease = next(value for value in outcomes if not isinstance(value, str))
    first = journal.prepare(stored.principal, lease, review, feedback=feedback)
    upload, _, _, _ = receipts(first.identity, first.payload.artifact, first.attempt)
    begun = journal.advance(stored.principal, lease, 1, "begun", upload.model_dump(mode="json"))
    barrier = Barrier(2)
    def stream(_):
        barrier.wait(timeout=5)
        try:
            return journal.advance(stored.principal, lease, begun.position, "streaming").position
        except ValueError as error:
            return str(error)
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(stream, range(2)), key=str) == [3, "result_position_conflict"]


def test_expired_fence_cannot_write_or_release_successor(stored):
    store, journal, selected, review, feedback = setup_result(stored)
    stale = store.acquire(stored.principal, selected.publication_id, seconds=1)
    first = journal.prepare(stored.principal, stale, review, feedback=feedback)
    time.sleep(1.1)
    current = store.acquire(stored.principal, selected.publication_id)
    assert current.fence == stale.fence + 1
    for operation in [lambda: store.guard(stored.principal, stale), lambda: store.renew(stored.principal, stale),
        lambda: store.release(stored.principal, stale), lambda: journal.prepare(stored.principal, stale, review, feedback=feedback),
        lambda: journal.advance(stored.principal, stale, 1, "rejected", {"reason": "denied"})]:
        with pytest.raises(ValueError, match="result_lease_lost"):
            operation()
    assert journal.read(stored.principal, selected.publication_id) == first
    assert store.renew(stored.principal, current).fence == current.fence


def test_payload_event_and_position_roll_back_together(stored, monkeypatch):
    store, journal, selected, review, feedback = setup_result(stored)
    lease = store.acquire(stored.principal, selected.publication_id)
    original = journal._append
    def fail(*args):
        original(*args)
        raise RuntimeError("injected after append")
    monkeypatch.setattr(journal, "_append", fail)
    with pytest.raises(RuntimeError, match="injected"):
        journal.prepare(stored.principal, lease, review, feedback=feedback)
    state = journal.read(stored.principal, selected.publication_id)
    assert state.payload is None and state.position == 0
    monkeypatch.setattr(journal, "_append", original)
    assert journal.prepare(stored.principal, lease, review, feedback=feedback).position == 1


@pytest.mark.parametrize("table", ["result_publications", "result_publication_payloads", "result_publication_events"])
@pytest.mark.parametrize("verb", ["UPDATE", "DELETE"])
def test_service_cannot_rewrite_result_history(stored, table, verb):
    command = ("UPDATE planning." + table + " SET publication_id='other'" if verb == "UPDATE" else "DELETE FROM planning." + table)
    with stored.engine.begin() as connection, pytest.raises(DBAPIError):
        connection.execute(text(command + " WHERE false"))


def test_expiry_at_actual_position_write_rolls_back_preparation(stored, monkeypatch):
    store, journal, selected, review, feedback = setup_result(stored)
    lease = store.acquire(stored.principal, selected.publication_id, seconds=1)
    original = journal._append
    def expire(*args):
        time.sleep(1.1)
        return original(*args)
    monkeypatch.setattr(journal, "_append", expire)
    with pytest.raises(ValueError, match="result_lease_or_position_lost"):
        journal.prepare(stored.principal, lease, review, feedback=feedback)
    state = journal.read(stored.principal, selected.publication_id)
    assert state.position == 0 and state.payload is None


def test_uncertain_stream_and_rejection_preserve_abandoned_upload_history(stored):
    store, journal, selected, review, feedback = setup_result(stored)
    lease = store.acquire(stored.principal, selected.publication_id)
    state = journal.prepare(stored.principal, lease, review, feedback=feedback)
    upload, _, _, _ = receipts(state.identity, state.payload.artifact, state.attempt)
    state = journal.advance(stored.principal, lease, state.position, "begun", upload.model_dump(mode="json"))
    state = journal.advance(stored.principal, lease, state.position, "streaming")
    first = state.attempt.identity
    state = journal.advance(stored.principal, lease, state.position, "abandoned")
    state = journal.advance(stored.principal, lease, state.position, "replacement")
    assert state.attempt.identity.ordinal == 2 and state.attempt.identity.begin_id != first.begin_id
    state = journal.advance(stored.principal, lease, state.position, "rejected", {"reason": "process_denied"})
    assert state.attempt.rejection == "process_denied" and len(state.events) == 6
    with pytest.raises(ValueError, match="publication_transition"):
        journal.advance(stored.principal, lease, state.position, "replacement")
    assert journal.read(stored.principal, selected.publication_id) == state


def test_read_only_actor_and_unknown_selection_cannot_acquire_or_prepare(stored):
    store, _journal, selected, _review, _feedback = setup_result(stored)
    reader = replace(stored.principal, actions=frozenset({"read_attempts"}))
    with pytest.raises(PermissionError):
        store.acquire(reader, selected.publication_id)
    with pytest.raises(PermissionError):
        store.register(reader, selected)
    with pytest.raises(ValueError, match="result_unknown"):
        store.acquire(stored.principal, "absent")
    with pytest.raises(ValueError, match="result_lease_seconds"):
        store.acquire(stored.principal, selected.publication_id, seconds=True)
