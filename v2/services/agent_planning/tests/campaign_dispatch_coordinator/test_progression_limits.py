"""Contention, expiry and rejected rounds remain explicit bounded work."""

import pytest
from amphora_agent_planning.campaign_dispatch.dispatcher import CompilerFenceLost

from .test_progression import setup

pytestmark = pytest.mark.postgres


def test_busy_selection_does_not_contact_peers(stored):
    owner, identity, _, refresh, runtime, registry = setup(stored)
    lease = owner.store.acquire(stored.principal, identity)
    busy = owner.advance(stored.principal, identity)
    assert busy.pause_reason == 'lease_unavailable' and not busy.terminal
    assert not runtime.sent and not registry.sent and refresh.calls == 0
    owner.store.release(stored.principal, lease)
    with pytest.raises(ValueError, match='compiler_selection_unknown'):
        owner.advance(stored.principal, 'absent-selection')
    with pytest.raises(ValueError, match='compiler_retry_policy'):
        owner.advance(stored.principal, identity, retry_rejected='yes')


def test_expired_terminal_round_gets_new_identity_without_rewriting_old_receipt(stored):
    owner, identity, journal, _, runtime, registry = setup(stored, tools=True)
    registry.expired = True
    first = owner.advance(stored.principal, identity)
    assert first.round.terminal
    registry.expired = False
    second = owner.advance(stored.principal, identity)
    assert second.stage == 'eligibility' and second.round.ordinal == 2 and not runtime.sent
    assert registry.sent[0] != registry.sent[1]
    assert journal.read_round(stored.principal, identity, first.round.check_id) == first.round


def test_rejected_check_requires_explicit_bounded_retry_policy(stored):
    owner, identity, _, _, runtime, registry = setup(stored, tools=True)
    registry.rejected = True
    first = owner.advance(stored.principal, identity)
    assert first.round.operations[0].progress.state == 'rejected'
    blocked = owner.advance(stored.principal, identity)
    assert blocked.pause_reason == 'eligibility_rejected' and len(registry.sent) == 1 and not runtime.sent
    registry.rejected = False
    retried = owner.advance(stored.principal, identity, retry_rejected=True)
    assert retried.round.ordinal == 2 and retried.round.terminal and len(registry.sent) == 2


@pytest.mark.parametrize('error', [CompilerFenceLost('lost'), ValueError('compiler_lease_lost')])
def test_local_fence_loss_is_explicit_and_owned_lease_is_cleaned_up(stored, monkeypatch, error):
    owner, identity, _, _, runtime, _ = setup(stored)
    def lose(principal, lease, *args, **kwargs):
        owner.store.release(principal, lease)
        raise error
    monkeypatch.setattr(owner.dispatcher, 'step', lose)
    result = owner.advance(stored.principal, identity)
    assert result.pause_reason == 'lease_lost' and not runtime.sent
    lease = owner.store.acquire(stored.principal, identity)
    owner.store.release(stored.principal, lease)


def test_unexpected_failure_propagates_but_releases_owned_lease(stored, monkeypatch):
    owner, identity, _, _, runtime, _ = setup(stored)
    def fail(*args, **kwargs):
        raise ValueError('fixture invariant failure')
    monkeypatch.setattr(owner.dispatcher, 'step', fail)
    with pytest.raises(ValueError, match='fixture invariant failure'):
        owner.advance(stored.principal, identity)
    assert not runtime.sent
    lease = owner.store.acquire(stored.principal, identity)
    owner.store.release(stored.principal, lease)
