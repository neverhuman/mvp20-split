"""Actual SQL command dependencies, immutable replay and atomic lease rollback."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_dispatch import CompilerEvent, CompilerObservation
from amphora_agent_planning.campaign_dispatch.journal import CompilerJournal
from amphora_agent_planning.campaign_dispatch.operations import CompilerOperations
from amphora_agent_planning.campaign_dispatch.store import CompilerStore
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from ..campaign_authoring.test_values import receipt, saved, validation
from ..campaign_eligibility.test_observations import response
from .support import setup

pytestmark = pytest.mark.postgres


def append(journal, principal, lease, state, action, data=None):
    event = CompilerEvent.record(state.effect, state.progress.position + 1, action, data)
    return journal.append(principal, lease, state.effect.effect_id, state.progress.position, event)


def observed(journal, principal, lease, state, receipt, readback=None):
    value = CompilerObservation.bind(lease.selection, state.effect, state.request, receipt, readback)
    return append(journal, principal, lease, state, 'observed', json.loads(value.canonical))


def test_save_validation_dependency_and_exact_replacement_history(stored):
    store, journal, lease, authoring = setup(stored)
    principal = stored.principal
    with pytest.raises(ValueError, match='compiler_saved_dependency'):
        journal.prepare_validation(principal, lease)
    first = journal.prepare_save(principal, lease)
    assert first.progress.state == 'prepared' and first == journal.prepare_save(principal, lease)
    sent = append(journal, principal, lease, first, 'dispatch')
    unknown = append(journal, principal, lease, sent, 'uncertain')
    unknown = append(journal, principal, lease, unknown, 'blocked', 'owner_unavailable')
    assert not unknown.terminal and unknown.progress.reason == 'owner_unavailable'
    with pytest.raises(ValueError, match='compiler_saved_dependency'):
        journal.prepare_validation(principal, lease)
    reply = saved(authoring)
    saved_state = observed(journal, principal, lease, unknown, reply.receipt, reply.readback)
    assert saved_state.terminal and saved_state.progress.state == 'saved'
    verify = journal.prepare_validation(principal, lease)
    compiled = observed(journal, principal, lease, verify, receipt(verify.request), validation(verify.request))
    assert compiled.progress.state == 'compiled'
    assert journal.prepare_validation(principal, lease) == compiled
    store.release(principal, lease)
    reader = replace(principal, actions=frozenset({'read_attempts'}))
    replacement = create_engine(stored.engine.url)
    try:
        owner = CompilerStore(replacement, store.runtime_owner, store.runtime_actor, store.eligibility)
        other = CompilerJournal(owner)
        for state in (saved_state, compiled):
            assert other.read(reader, lease.selection.effect_id, state.effect.effect_id) == state
    finally:
        replacement.dispose()
    assert journal.read(reader, lease.selection.effect_id, 'absent') is None


def test_same_append_replays_and_changed_append_conflicts(stored):
    _, journal, lease, _ = setup(stored)
    state = journal.prepare_save(stored.principal, lease)
    event = CompilerEvent.record(state.effect, 2, 'dispatch')
    first = journal.append(stored.principal, lease, state.effect.effect_id, 1, event)
    assert journal.append(stored.principal, lease, state.effect.effect_id, 1, event) == first
    changed = CompilerEvent.record(state.effect, 2, 'blocked', 'owner_unavailable')
    with pytest.raises(ValueError, match='compiler_event_conflict'):
        journal.append(stored.principal, lease, state.effect.effect_id, 1, changed)
    assert journal.read(stored.principal, lease.selection.effect_id, state.effect.effect_id) == first


def test_final_fence_expiry_rolls_back_new_operation(stored, monkeypatch):
    store, journal, lease, _ = setup(stored)
    store.release(stored.principal, lease)
    lease = store.acquire(stored.principal, lease.selection.effect_id, seconds=5)
    original = CompilerOperations.insert
    inserted = []
    def delayed(self, connection, key, effect, request):
        result = original(self, connection, key, effect, request)
        inserted.append(effect.effect_id)
        # Wait past the actual DB expiry in statements below the fixture's5s
        # statement timeout, without mutating the lease or faking its clock.
        for _ in range(2):
            remaining = connection.execute(text('SELECT greatest(0,extract(epoch FROM expires_at-clock_timestamp())) '
                'FROM planning.compiler_control WHERE selection_id=:selection'), key).scalar_one()
            if remaining <= 0:
                break
            connection.execute(text('SELECT pg_sleep(:seconds)'), {'seconds': min(4, float(remaining) + 0.05)})
        return result
    monkeypatch.setattr(CompilerOperations, 'insert', delayed)
    with pytest.raises(ValueError, match='compiler_lease_lost'):
        journal.prepare_save(stored.principal, lease)
    assert len(inserted) == 1
    with stored.engine.connect() as connection:
        count = connection.execute(text('SELECT count(*) FROM planning.compiler_effects WHERE selection_id=:selection'),
            {'selection': lease.selection.effect_id}).scalar_one()
    assert count == 0


def test_complete_round_replays_and_unresolved_checks_block_new_identity(stored):
    _, journal, lease, _ = setup(stored, tools=True)
    principal = stored.principal
    first = journal.prepare_round(principal, lease, 'first')
    assert first.ordinal == 1 and len(first.operations) == 1 and not first.terminal
    assert journal.prepare_round(principal, lease, 'first') == first
    with pytest.raises(ValueError, match='compiler_round_unresolved'):
        journal.prepare_round(principal, lease, 'second')
    state = first.operations[0]
    state = append(journal, principal, lease, state, 'dispatch')
    state = append(journal, principal, lease, state, 'uncertain')
    with pytest.raises(ValueError, match='compiler_round_unresolved'):
        journal.prepare_round(principal, lease, 'second')
    terminal = observed(journal, principal, lease, state, response(state.request))
    recorded = journal.read_round(principal, lease.selection.effect_id, 'first')
    assert recorded.terminal and recorded.operations == (terminal,)
    second = journal.prepare_round(principal, lease, 'second')
    assert second.ordinal == 2 and second.operations[0].effect.effect_id != terminal.effect.effect_id
    assert journal.read_round(principal, lease.selection.effect_id, 'first') == recorded


def test_zero_tool_round_does_not_create_empty_history(stored):
    _, journal, lease, _ = setup(stored)
    with pytest.raises(ValueError, match='compiler_round_tools'):
        journal.prepare_round(stored.principal, lease, 'empty')
    assert journal.read_round(stored.principal, lease.selection.effect_id, 'empty') is None
    assert journal.read_round(stored.principal, 'absent-selection', 'empty') is None
    assert journal.read(stored.principal, 'absent-selection', 'absent-effect') is None


def test_round_failure_rolls_back_header_and_commands(stored, monkeypatch):
    _, journal, lease, _ = setup(stored, tools=True)
    original = CompilerOperations.insert
    def fail_after_insert(self, connection, key, effect, request):
        original(self, connection, key, effect, request)
        raise RuntimeError('fixture interruption before round commit')
    monkeypatch.setattr(CompilerOperations, 'insert', fail_after_insert)
    with pytest.raises(RuntimeError, match='fixture interruption'):
        journal.prepare_round(stored.principal, lease, 'first')
    assert journal.read_round(stored.principal, lease.selection.effect_id, 'first') is None
    with stored.engine.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM planning.compiler_effects WHERE selection_id=:selection'),
            {'selection': lease.selection.effect_id}).scalar_one() == 0


def test_service_cannot_rewrite_effect_or_event_history(stored):
    _, journal, lease, _ = setup(stored)
    first = journal.prepare_save(stored.principal, lease)
    for table in ('compiler_effects', 'compiler_events', 'compiler_rounds'):
        for statement in (f'DELETE FROM planning.{table} WHERE selection_id=:selection',
                          f'UPDATE planning.{table} SET selection_id=selection_id WHERE selection_id=:selection'):
            with pytest.raises(DBAPIError), stored.engine.begin() as connection:
                connection.execute(text(statement), {'selection': lease.selection.effect_id})
    assert journal.read(stored.principal, lease.selection.effect_id, first.effect.effect_id) == first


def test_origin_reuse_never_reuses_mutable_progress_or_permissions(stored, monkeypatch):
    _, journal, lease, _ = setup(stored)
    from amphora_agent_planning.campaign_dispatch.history import CompilerHistory
    original = CompilerHistory.load
    calls = []
    def load(*args):
        calls.append(args[1].actions)
        return original(*args)
    monkeypatch.setattr(CompilerHistory, 'load', load)
    first = journal.prepare_save(stored.principal, lease)
    changed = append(journal, stored.principal, lease, first, 'dispatch')
    assert journal.read(stored.principal, lease.selection.effect_id, first.effect.effect_id) == changed
    assert len(calls) == 1
    reader = replace(stored.principal, actions=frozenset({'read_attempts'}))
    assert journal.read(reader, lease.selection.effect_id, first.effect.effect_id) == changed
    assert len(calls) == 2
    with pytest.raises(PermissionError):
        journal.read(replace(reader, actions=frozenset()), lease.selection.effect_id, first.effect.effect_id)
    assert len(calls) == 2


def test_sixteen_round_bound_preserves_prior_complete_history(stored):
    _, journal, lease, _ = setup(stored, tools=True)
    first = None
    for ordinal in range(1, 17):
        check_id = 'round-' + str(ordinal)
        current = journal.prepare_round(stored.principal, lease, check_id)
        assert current.ordinal == ordinal
        state = current.operations[0]
        observed(journal, stored.principal, lease, state, response(state.request))
        if first is None:
            first = journal.read_round(stored.principal, lease.selection.effect_id, check_id)
    with pytest.raises(ValueError, match='compiler_round_limit'):
        journal.prepare_round(stored.principal, lease, 'round-17')
    assert journal.read_round(stored.principal, lease.selection.effect_id, 'round-1') == first


def test_derived_batch_cache_is_bounded_and_safe_for_concurrent_checks(stored):
    _, journal, lease, _ = setup(stored, tools=True)
    operations = journal.context(stored.principal, lease.selection)
    names = ['check-' + str(index) for index in range(8)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(operations.batch, names))
    for name, batch in zip(names, results, strict=True):
        assert len(batch) == 1 and batch[0][1].check_id == name
        assert batch[0][0].document().check_id == name
        assert operations.batch(name) == batch
    assert len(operations._batches) <= 2
