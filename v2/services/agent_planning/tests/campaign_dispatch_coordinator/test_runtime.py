"""Owned SQL plus scripted Runtime: recovery never creates fresh authority."""

import pytest
from amphora_agent_planning.campaign_authoring import AuthoringOutcome
from amphora_agent_planning.campaign_dispatch.dispatcher import CompilerFenceLost
from amphora_agent_planning.campaign_exchanges import (
    ExchangeAbsent,
    ExchangeConflict,
    ExchangeDenied,
    ExchangeUnavailable,
)

from ..campaign_authoring.test_values import receipt, saved
from .support import fixture

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('valid', [True, False])
def test_journal_before_post_then_exact_save_and_validation(stored, valid):
    _, journal, lease, dispatcher, refresh, runtime, _ = fixture(stored)
    first = journal.prepare_save(stored.principal, lease)
    def before_send():
        actual = journal.read(stored.principal, lease.selection.effect_id, first.effect.effect_id)
        assert actual.progress.state == 'dispatching' and actual.effect == first.effect
    runtime.before_send = before_send
    result = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert result.operation.progress.state == 'saved' and len(runtime.sent) == 1 and refresh.calls == 1
    runtime.before_send, runtime.valid = None, valid
    second = journal.prepare_validation(stored.principal, lease)
    result = dispatcher.step(stored.principal, lease, second.effect.effect_id)
    assert result.operation.progress.state == ('compiled' if valid else 'structural_invalid')
    assert len(runtime.sent) == 2 and refresh.calls == 2
    assert dispatcher.step(stored.principal, lease, second.effect.effect_id).operation == result.operation
    assert len(runtime.sent) == 2


def test_committed_lost_reply_reconciles_when_current_processing_denied(stored):
    _, journal, lease, dispatcher, refresh, runtime, _ = fixture(stored)
    first = journal.prepare_save(stored.principal, lease)
    runtime.lose_reply = True
    unknown = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert unknown.operation.progress.state == 'uncertain' and len(runtime.sent) == 1
    refresh.denied = True
    recovered = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert recovered.operation.progress.state == 'saved'
    assert len(runtime.sent) == 1 and refresh.calls == 1
    assert recovered.operation.effect == first.effect


def test_unissued_write_requires_current_processing(stored):
    _, journal, lease, dispatcher, refresh, runtime, _ = fixture(stored)
    first = journal.prepare_save(stored.principal, lease)
    refresh.denied = True
    blocked = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert blocked.pause_reason == 'input_unavailable' and not runtime.sent
    assert blocked.operation.progress.dispatches == 0
    assert dispatcher.step(stored.principal, lease, first.effect.effect_id).operation == blocked.operation


@pytest.mark.parametrize(('error', 'reason'), [(ExchangeDenied('denied'), 'owner_access_denied'),
    (ExchangeUnavailable('unknown'), 'owner_unavailable'), (ValueError('malformed receipt'), 'owner_protocol'),
    (ExchangeConflict('conflict'), 'identity_conflict'),
    (ExchangeUnavailable('compiler_response_protocol'), 'owner_protocol')])
def test_read_failure_never_proves_absence_or_permits_post(stored, error, reason):
    _, journal, lease, dispatcher, refresh, runtime, _ = fixture(stored)
    first = journal.prepare_save(stored.principal, lease)
    runtime.receipt_error = error
    result = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert result.pause_reason == reason and not runtime.sent and refresh.calls == 0


def test_pending_receipt_is_retried_only_with_original_bytes_and_fresh_checks(stored):
    _, journal, lease, dispatcher, refresh, runtime, _ = fixture(stored)
    first = journal.prepare_save(stored.principal, lease)
    runtime.outcomes[first.request.canonical] = AuthoringOutcome.bind(first.request, receipt(first.request, 'pending'))
    result = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert result.operation.progress.state == 'saved'
    assert runtime.sent == [first.request.canonical] and refresh.calls == 1


def test_accepted_receipt_with_missing_readback_cannot_be_resubmitted(stored):
    _, journal, lease, dispatcher, refresh, runtime, _ = fixture(stored)
    first = journal.prepare_save(stored.principal, lease)
    runtime.outcomes[first.request.canonical] = saved(runtime.authoring)
    runtime.read_error = ExchangeAbsent('readback missing')
    partial = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert partial.pause_reason == 'dependency_unavailable'
    assert partial.operation.progress.observation.status == 'awaiting_readback'
    runtime.receipt_error = ExchangeAbsent('receipt no longer available')
    runtime.read_error, refresh.denied = None, True
    recovered = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert recovered.operation.progress.state == 'saved'
    assert not runtime.sent and refresh.calls == 0


def test_fence_loss_before_transmission_is_not_a_peer_error(stored):
    store, journal, lease, dispatcher, _, runtime, _ = fixture(stored)
    first = journal.prepare_save(stored.principal, lease)
    runtime.before_send = lambda: store.release(stored.principal, lease)
    with pytest.raises(CompilerFenceLost):
        dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert not runtime.sent
    retained = journal.read(stored.principal, lease.selection.effect_id, first.effect.effect_id)
    assert retained.progress.state == 'dispatching' and retained.progress.dispatches == 1
