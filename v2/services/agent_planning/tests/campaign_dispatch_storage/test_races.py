"""Competing writers and replacement owners preserve exact compiler history."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_agent_planning.campaign_dispatch import CompilerEvent
from amphora_agent_planning.campaign_dispatch.journal import CompilerJournal
from amphora_agent_planning.campaign_dispatch.store import CompilerStore
from sqlalchemy import create_engine, text

from .support import setup

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('identical', [True, False])
def test_competing_appends_keep_one_exact_event(stored, identical):
    _, journal, lease, _ = setup(stored)
    first = journal.prepare_save(stored.principal, lease)
    events = [CompilerEvent.record(first.effect, 2, 'dispatch'),
              CompilerEvent.record(first.effect, 2, 'dispatch' if identical else 'blocked',
                                   None if identical else 'owner_unavailable')]
    barrier = Barrier(2)
    def write(event):
        barrier.wait(timeout=10)
        try:
            return journal.append(stored.principal, lease, first.effect.effect_id, 1, event)
        except ValueError as error:
            assert str(error) == 'compiler_event_conflict'
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(write, events))
    accepted = [item for item in results if item is not None]
    assert len(accepted) == (2 if identical else 1)
    current = journal.read(stored.principal, lease.selection.effect_id, first.effect.effect_id)
    assert all(item == current for item in accepted)
    assert current.progress.position == 2 and len(current.events) == 2
    assert current.events[0] == first.events[0]
    assert current.events[1].event in events


def test_replacement_holder_rejects_all_old_journal_writes(stored):
    store, journal, old, _ = setup(stored, tools=True)
    first = journal.prepare_save(stored.principal, old)
    store.release(stored.principal, old)
    current = store.acquire(stored.principal, old.selection.effect_id, seconds=300)
    event = CompilerEvent.record(first.effect, 2, 'dispatch')
    for action in (lambda: journal.prepare_save(stored.principal, old),
                   lambda: journal.prepare_validation(stored.principal, old),
                   lambda: journal.prepare_round(stored.principal, old, 'stale'),
                   lambda: journal.append(stored.principal, old, first.effect.effect_id, 1, event)):
        with pytest.raises(ValueError, match='compiler_lease_lost'):
            action()
    assert journal.read_round(stored.principal, old.selection.effect_id, 'stale') is None
    assert journal.read(stored.principal, old.selection.effect_id, first.effect.effect_id) == first
    replacement = create_engine(stored.engine.url)
    try:
        other = CompilerJournal(CompilerStore(replacement, store.runtime_owner, store.runtime_actor, store.eligibility))
        advanced = other.append(stored.principal, current, first.effect.effect_id, 1, event)
        assert advanced.progress.position == 2
        assert journal.read(stored.principal, old.selection.effect_id, first.effect.effect_id) == advanced
    finally:
        replacement.dispose()


def test_read_and_write_authority_remains_scoped(stored):
    _, journal, lease, _ = setup(stored)
    first = journal.prepare_save(stored.principal, lease)
    wrong_actor = replace(stored.principal, actor_id='foreign')
    with pytest.raises(ValueError, match='compiler_selection_actor'):
        journal.read(wrong_actor, lease.selection.effect_id, first.effect.effect_id)
    foreign_scope = replace(stored.principal, scope=stored.principal.scope.model_copy(update={'project_id': 'foreign'}))
    assert journal.read(foreign_scope, lease.selection.effect_id, first.effect.effect_id) is None
    with pytest.raises(PermissionError):
        journal.prepare_save(foreign_scope, lease)
    reader = replace(stored.principal, actions=frozenset({'read_attempts'}))
    assert journal.read(reader, lease.selection.effect_id, first.effect.effect_id) == first
    with pytest.raises(PermissionError):
        journal.append(reader, lease, first.effect.effect_id, 1, CompilerEvent.record(first.effect, 2, 'dispatch'))


def test_corrupt_mutable_projection_fails_closed_without_rewriting_history(stored):
    _, journal, lease, _ = setup(stored)
    first = journal.prepare_save(stored.principal, lease)
    params = {'tenant': stored.principal.scope.tenant_id, 'project': stored.principal.scope.project_id,
              'selection': lease.selection.effect_id, 'effect': first.effect.effect_id}
    where = 'tenant_id=:tenant AND project_id=:project AND selection_id=:selection AND effect_id=:effect'
    with stored.engine.begin() as connection:
        connection.execute(text('UPDATE planning.compiler_effect_control SET position=2 WHERE ' + where), params)
    with pytest.raises(ValueError, match='compiler_stored_position'):
        journal.read(stored.principal, lease.selection.effect_id, first.effect.effect_id)
    with pytest.raises(ValueError, match='compiler_stored_position'):
        journal.append(stored.principal, lease, first.effect.effect_id, 1, CompilerEvent.record(first.effect, 2, 'dispatch'))
    with stored.engine.connect() as connection:
        rows = connection.execute(text('SELECT canonical_bytes FROM planning.compiler_events WHERE ' + where), params).scalars().all()
    assert [bytes(row) for row in rows] == [first.events[0].event.canonical]
