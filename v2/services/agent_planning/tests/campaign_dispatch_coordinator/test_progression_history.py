"""Progression retains bounded rounds, terminal rejection and scoped history."""

from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_authoring import AuthoringOutcome

from ..campaign_authoring.test_values import receipt
from ..campaign_dispatch_storage.test_journal import observed
from ..campaign_eligibility.test_observations import response
from .test_progression import setup

pytestmark = pytest.mark.postgres


def test_sixteen_rejected_rounds_exhaust_without_allocating_another_command(stored):
    owner, identity, journal, _, runtime, registry = setup(stored, tools=True)
    lease = owner.store.acquire(stored.principal, identity, seconds=300)
    for ordinal in range(1, 17):
        current = journal.prepare_round(stored.principal, lease, 'planning-check-' + str(ordinal))
        operation = current.operations[0]
        reply = response(operation.request, change=lambda value: value.update(status='rejected', reason_code='no_capacity'))
        observed(journal, stored.principal, lease, operation, reply)
    owner.store.release(stored.principal, lease)
    before = journal.latest_round(stored.principal, identity)
    result = owner.advance(stored.principal, identity, retry_rejected=True)
    assert result.pause_reason == 'round_limit' and result.round == before and before.ordinal == 16
    assert not result.terminal and not runtime.sent and not registry.sent
    assert journal.latest_round(stored.principal, identity) == before


def test_terminal_runtime_rejection_never_starts_a_tool_round(stored):
    owner, identity, journal, refresh, runtime, registry = setup(stored, tools=True)
    lease = owner.store.acquire(stored.principal, identity)
    operation = journal.prepare_save(stored.principal, lease)
    owner.store.release(stored.principal, lease)
    runtime.outcomes[operation.request.canonical] = AuthoringOutcome.bind(operation.request, receipt(operation.request, 'rejected'))
    result = owner.advance(stored.principal, identity)
    assert result.stage == 'save' and result.terminal and result.dispatch.operation.progress.state == 'rejected'
    assert journal.latest_round(stored.principal, identity) is None
    assert not runtime.sent and not registry.sent and refresh.calls == 0


def test_latest_round_read_preserves_original_actor_scope_and_grants(stored):
    owner, identity, journal, _, _, _ = setup(stored, tools=True)
    first = owner.advance(stored.principal, identity)
    reader = replace(stored.principal, actions=frozenset({'read_attempts'}))
    assert journal.latest_round(reader, identity) == first.round
    with pytest.raises(ValueError, match='compiler_selection_actor'):
        journal.latest_round(replace(reader, actor_id='another'), identity)
    with pytest.raises(PermissionError):
        journal.latest_round(replace(reader, actions=frozenset()), identity)
    foreign = replace(reader, scope=reader.scope.model_copy(update={'project_id': 'foreign'}))
    assert journal.latest_round(foreign, identity) is None
