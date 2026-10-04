"""Actual owned PostgreSQL histories; owner records are scripted evidence."""

import json
import time
from dataclasses import replace

import pytest
from amphora_agent_planning.owner_handoff.journal import HandoffJournal
from amphora_agent_planning.owner_handoff.receipt import OwnerOutcome
from amphora_agent_planning.owner_handoff.selection import HandoffSelection
from amphora_agent_planning.owner_handoff.store import HandoffStore
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from ..result_publication.test_prepared import answer_history

pytestmark = pytest.mark.postgres


def setup_handoff(stored):
    _, result, review, questions = answer_history(stored)
    selected = HandoffSelection.bind(stored.principal, result.trace(), "publication", "question", "q", "research")
    store = HandoffStore(stored.engine, "research", trace_publisher_id="data-owner")
    store.register(stored.principal, selected)
    return store, HandoffJournal(store), selected, review, questions


def acknowledge(journal, principal, lease, state):
    outcome = OwnerOutcome.research(state.payload.request, state.payload.request.document())
    return journal.advance(principal, lease, state.position, "observed", json.loads(outcome.canonical))


def test_exact_preparation_dispatch_and_outcome_survive_replacement(stored):
    store, journal, selected, review, questions = setup_handoff(stored)
    assert store.register(stored.principal, selected) == selected
    assert journal.read(stored.principal, selected.effect_id).payload is None
    assert journal.read(stored.principal, "unknown") is None
    lease = store.acquire(stored.principal, selected.effect_id)
    state = journal.prepare(stored.principal, lease, review, questions=questions)
    assert journal.prepare(stored.principal, lease, review, questions=questions) == state
    state = journal.advance(stored.principal, lease, state.position, "dispatch")
    assert state.progress.dispatches == 1
    state = journal.advance(stored.principal, lease, state.position, "uncertain")
    state = acknowledge(journal, stored.principal, lease, state)
    store.release(stored.principal, lease)
    engine = create_engine(stored.engine.url)
    try:
        replacement = HandoffJournal(HandoffStore(engine, "research", trace_publisher_id="data-owner"))
        reader = replace(stored.principal, actions=frozenset({"read_attempts"}))
        assert replacement.read(reader, selected.effect_id) == state
        assert state.terminal and state.progress.state == "acknowledged"
    finally:
        engine.dispose()


def test_local_need_requires_exact_acknowledged_question(stored):
    store, journal, selected, review, questions = setup_handoff(stored)
    need = HandoffSelection.bind(stored.principal, selected.trace(), "publication", "need", "n", "research")
    store.register(stored.principal, need)
    lease = store.acquire(stored.principal, need.effect_id)
    with pytest.raises(ValueError, match="handoff_dependency_unacknowledged"):
        journal.prepare(stored.principal, lease, review, questions=questions)
    assert journal.read(stored.principal, need.effect_id).position == 0
    question_lease = store.acquire(stored.principal, selected.effect_id)
    state = journal.prepare(stored.principal, question_lease, review, questions=questions)
    acknowledge(journal, stored.principal, question_lease, state)
    store.release(stored.principal, question_lease)
    state = journal.prepare(stored.principal, lease, review, questions=questions)
    assert state.payload.request.kind == "need"
    assert journal.advance(stored.principal, lease, state.position, "dispatch").progress.dispatches == 1
    store.release(stored.principal, lease)


def test_changed_selection_owner_and_actor_are_rejected(stored):
    store, journal, selected, _, _ = setup_handoff(stored)
    alternate = HandoffSelection.bind(stored.principal, selected.trace(), "other", "question", "q", "research")
    with pytest.raises(ValueError, match="handoff_selection_conflict"):
        store.register(stored.principal, alternate)
    with pytest.raises(ValueError, match="handoff_configuration_conflict"):
        HandoffJournal(HandoffStore(stored.engine, "other", trace_publisher_id="data-owner")).read(stored.principal, selected.effect_id)
    with pytest.raises(ValueError, match="handoff_actor_binding"):
        journal.read(replace(stored.principal, actor_id="other"), selected.effect_id)
    with pytest.raises(PermissionError):
        store.acquire(replace(stored.principal, actions=frozenset({"read_attempts"})), selected.effect_id)


def test_expired_fence_cannot_mutate_or_release_successor(stored):
    store, journal, selected, review, questions = setup_handoff(stored)
    lease = store.acquire(stored.principal, selected.effect_id, seconds=1)
    with pytest.raises(ValueError, match="handoff_lease_unavailable"):
        store.acquire(stored.principal, selected.effect_id)
    time.sleep(1.05)
    with pytest.raises(ValueError, match="handoff_lease_lost"):
        journal.prepare(stored.principal, lease, review, questions=questions)
    successor = store.acquire(stored.principal, selected.effect_id)
    successor = store.renew(stored.principal, successor)
    store.guard(stored.principal, successor)
    for operation in (store.release, store.guard, store.renew):
        with pytest.raises(ValueError, match="handoff_lease_lost"):
            operation(stored.principal, lease)
    state = journal.prepare(stored.principal, successor, review, questions=questions)
    with pytest.raises(ValueError, match="handoff_position_conflict"):
        journal.advance(stored.principal, successor, state.position + 1, "dispatch")
    store.release(stored.principal, successor)


def test_expiry_at_final_cas_rolls_back_payload_and_event(stored, monkeypatch):
    store, journal, selected, review, questions = setup_handoff(stored)
    lease = store.acquire(stored.principal, selected.effect_id, seconds=1)
    original = journal._append
    def delayed(connection, key, previous, event):
        time.sleep(1.05)
        return original(connection, key, previous, event)
    monkeypatch.setattr(journal, "_append", delayed)
    with pytest.raises(ValueError, match="handoff_lease_or_position_lost"):
        journal.prepare(stored.principal, lease, review, questions=questions)
    assert journal.read(stored.principal, selected.effect_id).position == 0
    assert journal.read(stored.principal, selected.effect_id).payload is None


@pytest.mark.parametrize("table", ["owner_handoffs", "owner_handoff_payloads", "owner_handoff_events", "owner_handoff_control"])
def test_service_cannot_delete_history_or_change_identity(stored, table):
    setup_handoff(stored)
    for sql in (f"DELETE FROM planning.{table} WHERE false", f"UPDATE planning.{table} SET effect_id='changed' WHERE false"):
        with stored.engine.begin() as connection, pytest.raises(DBAPIError) as caught:
            connection.execute(text(sql))
        assert caught.value.orig.sqlstate == "42501"


def test_two_concurrent_acquirers_have_one_fence_owner(stored):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    store, _, selection, _, _ = setup_handoff(stored)
    barrier = Barrier(2)
    def acquire():
        barrier.wait()
        try:
            return store.acquire(stored.principal, selection.effect_id)
        except ValueError as error:
            assert str(error) == "handoff_lease_unavailable"
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(acquire) for _ in range(2)]
        results = [future.result() for future in futures]
    winners = [lease for lease in results if lease is not None]
    assert len(winners) == 1
    store.release(stored.principal, winners[0])


def test_last_event_slot_can_only_commit_terminal_readback(stored):
    store, journal, selected, review, questions = setup_handoff(stored)
    lease = store.acquire(stored.principal, selected.effect_id, seconds=120)
    state = journal.prepare(stored.principal, lease, review, questions=questions)
    while state.position < 63:
        state = journal.advance(stored.principal, lease, state.position, "blocked", "owner_unavailable")
    with pytest.raises(ValueError, match="handoff_terminal_slot_reserved"):
        journal.advance(stored.principal, lease, state.position, "dispatch")
    assert journal.read(stored.principal, selected.effect_id) == state
    state = acknowledge(journal, stored.principal, lease, state)
    assert state.position == 64 and state.terminal
    store.release(stored.principal, lease)
