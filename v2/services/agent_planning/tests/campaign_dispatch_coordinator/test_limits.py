"""Bounded histories and last-moment expiry cannot authorize another write."""

from datetime import UTC, datetime, timedelta

import pytest
from amphora_agent_planning.campaign_authoring import AuthoringOutcome
from amphora_agent_planning.campaign_dispatch import CompilerEvent
from amphora_agent_planning.campaign_dispatch import dispatcher as module
from amphora_agent_planning.campaign_dispatch.operations import CompilerOperations
from amphora_agent_planning.campaign_exchanges import (
    ExchangeDenied,
    ExchangeUnavailable,
)
from sqlalchemy import text

from ..campaign_authoring.test_values import receipt, saved
from .support import fixture

pytestmark = pytest.mark.postgres


def test_final_event_slot_is_reserved_for_terminal_recovery(stored):
    store, journal, lease, dispatcher, _, runtime, _ = fixture(stored)
    first = journal.prepare_save(stored.principal, lease)
    key = store.key(stored.principal, lease.selection.effect_id) | {'effect': first.effect.effect_id}
    # Seed a valid exhausted history through the owner's granted INSERT/control
    # columns, then exercise production replay. No immutable row is altered.
    with stored.engine.begin() as connection:
        store.lock(connection, key)
        for position in range(2, 64):
            event = CompilerEvent.record(first.effect, position, 'blocked', 'owner_unavailable')
            CompilerOperations.insert_event(connection, key, event, position)
        connection.execute(text('UPDATE planning.compiler_effect_control SET position=63 WHERE '
            'tenant_id=:tenant AND project_id=:project AND selection_id=:selection AND effect_id=:effect'), key)
    limited = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert limited.pause_reason == 'event_limit' and not runtime.sent
    runtime.receipt_error = ExchangeDenied('denied')
    assert dispatcher.step(stored.principal, lease, first.effect.effect_id).pause_reason == 'event_limit'
    runtime.receipt_error = None
    runtime.outcomes[first.request.canonical] = AuthoringOutcome.bind(first.request, receipt(first.request, 'pending'))
    assert dispatcher.step(stored.principal, lease, first.effect.effect_id).pause_reason == 'event_limit'
    runtime.outcomes[first.request.canonical] = saved(runtime.authoring)
    recovered = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert recovered.operation.progress.state == 'saved' and recovered.operation.progress.position == 64
    assert not runtime.sent


def test_candidate_expiring_after_preparation_is_checked_before_send(stored, monkeypatch):
    _, journal, lease, dispatcher, _, runtime, _ = fixture(stored, tools=True)
    current = journal.prepare_round(stored.principal, lease, 'check-1')
    assert dispatcher.step(stored.principal, lease, current.operations[0].effect.effect_id).operation.terminal
    first = journal.prepare_save(stored.principal, lease)
    class ExpiredClock:
        @staticmethod
        def now(zone):
            return datetime.now(UTC) + timedelta(seconds=60)
    monkeypatch.setattr(module, 'datetime', ExpiredClock)
    result = dispatcher.step(stored.principal, lease, first.effect.effect_id, check_id='check-1')
    assert result.pause_reason == 'eligibility_expired' and not runtime.sent
    assert result.operation.progress.dispatches == 1


@pytest.mark.parametrize('failure', ['readback', 'binding', 'protocol'])
def test_committed_partial_or_malformed_reply_recovers_without_new_post(stored, monkeypatch, failure):
    _, journal, lease, dispatcher, refresh, runtime, _ = fixture(stored)
    first = journal.prepare_save(stored.principal, lease)
    if failure == 'readback':
        runtime.read_error = ExchangeUnavailable('readback unavailable')
    else:
        original = runtime.submit
        def malformed(*args, **kwargs):
            original(*args, **kwargs)
            if failure == 'protocol':
                raise ExchangeUnavailable('compiler_response_protocol')
            raise ValueError('malformed peer receipt')
        monkeypatch.setattr(runtime, 'submit', malformed)
    blocked = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert blocked.pause_reason == ('owner_unavailable' if failure == 'readback' else 'owner_protocol')
    assert len(runtime.sent) == 1
    refresh.denied, runtime.read_error = True, None
    recovered = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert recovered.operation.progress.state == 'saved' and len(runtime.sent) == 1


def test_original_rejection_is_terminal_without_fresh_processing_or_post(stored):
    _, journal, lease, dispatcher, refresh, runtime, _ = fixture(stored)
    first = journal.prepare_save(stored.principal, lease)
    runtime.outcomes[first.request.canonical] = AuthoringOutcome.bind(first.request, receipt(first.request, 'rejected'))
    refresh.denied = True
    rejected = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert rejected.operation.progress.state == 'rejected' and not runtime.sent and refresh.calls == 0
