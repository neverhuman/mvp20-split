"""Actual owned SQL preserves origin, immutable selections and fenced leases."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_agent_planning.campaign_authoring import AuthoringPlan
from amphora_agent_planning.campaign_dispatch import CompilerSelection
from amphora_agent_planning.campaign_dispatch.history import CompilerHistory
from amphora_agent_planning.campaign_dispatch.store import CompilerStore
from amphora_agent_planning.campaign_eligibility import EligibilityConfiguration
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from ..campaign_handoff_storage.test_origin import seeded

pytestmark = pytest.mark.postgres


def setup(stored, *, omit=None):
    review, budget = seeded(stored, omit=omit)
    authoring = AuthoringPlan.bind(review, budget, owner_id='runtime', actor_id='planning-agent')
    config = EligibilityConfiguration.bind(owner_id='registry', actor_id='planning-agent', policy_sha256='e' * 64)
    selection = CompilerSelection.bind(stored.principal, authoring, config)
    return CompilerStore(stored.engine, 'runtime', 'planning-agent', config), selection, authoring, config


def test_original_history_selection_retry_and_replacement(stored):
    store, selection, authoring, config = setup(stored)
    history = CompilerHistory.load(stored.engine, stored.principal, selection)
    assert history.authoring == authoring and history.eligibility == config
    assert history.origin.settlement.charge.accounting_units == 60
    original = store.register(stored.principal, selection)
    assert original == store.register(stored.principal, selection)
    reader = replace(stored.principal, actions=frozenset({'read_attempts'}))
    assert store.read(reader, selection.effect_id) == original
    replacement = create_engine(stored.engine.url)
    try:
        new = CompilerStore(replacement, 'runtime', 'planning-agent', config)
        assert new.read(reader, selection.effect_id) == original
        assert CompilerHistory.load(replacement, reader, selection) == history
    finally:
        replacement.dispose()
    with pytest.raises(PermissionError):
        store.register(reader, selection)


@pytest.mark.parametrize('omit', ['request', 'preparation', 'reservation', 'observation', 'settlement'])
def test_missing_original_history_cannot_create_selection(stored, omit):
    store, selection, _, _ = setup(stored, omit=omit)
    with pytest.raises(ValueError):
        store.register(stored.principal, selection)
    assert store.read(stored.principal, selection.effect_id) is None


def test_changed_configuration_conflicts_in_same_original_slot(stored):
    store, selection, authoring, config = setup(stored)
    original = store.register(stored.principal, selection)
    changed = replace(authoring, owner_id='new-runtime')
    other = CompilerSelection.bind(stored.principal, changed, config)
    assert other.effect_id == selection.effect_id
    new = CompilerStore(stored.engine, 'new-runtime', 'planning-agent', config)
    with pytest.raises(ValueError, match='compiler_configuration_conflict'):
        new.register(stored.principal, other)
    assert store.read(stored.principal, selection.effect_id) == original


def test_competing_leases_have_one_holder_and_old_fence_cannot_advance(stored):
    store, selection, _, _ = setup(stored)
    store.register(stored.principal, selection)
    barrier = Barrier(2)
    def acquire():
        barrier.wait(timeout=5)
        try:
            return store.acquire(stored.principal, selection.effect_id)
        except ValueError as error:
            assert str(error) == 'compiler_lease_unavailable'
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        leases = list(pool.map(lambda _: acquire(), range(2)))
    assert sum(lease is not None for lease in leases) == 1
    first = next(lease for lease in leases if lease is not None)
    store.guard(stored.principal, first)
    renewed = store.renew(stored.principal, first)
    assert renewed.fence == first.fence and renewed.holder == first.holder and renewed.expires_at >= first.expires_at
    store.release(stored.principal, renewed)
    current = store.acquire(stored.principal, selection.effect_id)
    assert current.fence == first.fence + 1 and current.holder != first.holder
    for action in (store.guard, store.renew, store.release):
        with pytest.raises(ValueError, match='compiler_lease_lost'):
            action(stored.principal, first)
    store.guard(stored.principal, current)
    store.release(stored.principal, current)


def test_database_clock_expiry_cannot_be_renewed(stored):
    store, selection, _, _ = setup(stored)
    store.register(stored.principal, selection)
    lease = store.acquire(stored.principal, selection.effect_id, seconds=1)
    with stored.engine.connect() as connection:
        connection.execute(text('SELECT pg_sleep(1.1)'))
    for action in (store.guard, store.renew, store.release):
        with pytest.raises(ValueError, match='compiler_lease_lost'):
            action(stored.principal, lease)
    replacement = store.acquire(stored.principal, selection.effect_id)
    assert replacement.fence == lease.fence + 1
    store.release(stored.principal, replacement)


def test_wrong_actor_and_missing_grants_cannot_read_or_claim(stored):
    store, selection, _, _ = setup(stored)
    store.register(stored.principal, selection)
    other = replace(stored.principal, actor_id='other')
    with pytest.raises(ValueError, match='compiler_selection_actor'):
        store.read(other, selection.effect_id)
    with pytest.raises(ValueError, match='compiler_selection_actor'):
        store.acquire(other, selection.effect_id)
    reader = replace(stored.principal, actions=frozenset({'read_attempts'}))
    with pytest.raises(PermissionError):
        store.acquire(reader, selection.effect_id)
    with pytest.raises(PermissionError):
        store.read(replace(reader, actions=frozenset()), selection.effect_id)
    foreign = replace(stored.principal, scope=stored.principal.scope.model_copy(update={'project_id': 'foreign'}))
    assert store.read(foreign, selection.effect_id) is None


def test_service_cannot_rewrite_or_delete_history(stored):
    store, selection, _, _ = setup(stored)
    original = store.register(stored.principal, selection)
    key = store.key(stored.principal, selection.effect_id)
    for sql in ["UPDATE planning.compiler_selections SET actor_id='changed' WHERE selection_id=:selection",
                'DELETE FROM planning.compiler_selections WHERE selection_id=:selection',
                "UPDATE planning.compiler_control SET selection_id='changed' WHERE selection_id=:selection"]:
        with pytest.raises(DBAPIError), stored.engine.begin() as connection:
            connection.execute(text(sql), key)
    assert store.read(stored.principal, selection.effect_id) == original


@pytest.mark.parametrize('seconds', [0, 301, True])
def test_invalid_lease_bounds_reject(stored, seconds):
    store, selection, _, _ = setup(stored)
    with pytest.raises(ValueError, match='compiler_lease_seconds'):
        store.acquire(stored.principal, selection.effect_id, seconds)
