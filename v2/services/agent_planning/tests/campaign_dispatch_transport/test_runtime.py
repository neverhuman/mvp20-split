"""Real HTTP clients and owned SQL across committed-but-unacknowledged writes."""

import pytest
from amphora_agent_planning.campaign_dispatch.progression import CompilerProgression

from .support import hosted

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize('valid', [True, False])
def test_save_validate_and_terminal_replay(stored, valid):
    with hosted(stored) as (_, journal, lease, dispatcher, _, peer):
        peer.valid = valid
        saving = journal.prepare_save(stored.principal, lease)
        peer.register(saving)
        assert dispatcher.step(stored.principal, lease, saving.effect.effect_id).operation.progress.state == 'saved'
        validating = journal.prepare_validation(stored.principal, lease)
        peer.register(validating)
        result = dispatcher.step(stored.principal, lease, validating.effect.effect_id)
        assert result.operation.progress.state == ('compiled' if valid else 'structural_invalid')
        count = len(peer.calls)
        replay = dispatcher.step(stored.principal, lease, validating.effect.effect_id)
        assert replay.operation == result.operation and replay.prerequisites is None
        assert len(peer.posts) == 2 and len(peer.calls) == count


@pytest.mark.parametrize('loss', ['disconnect', 'malformed'])
def test_lost_commit_recovers_read_only_despite_current_denial(stored, loss):
    with hosted(stored) as (_, journal, lease, dispatcher, refresh, peer):
        saving = journal.prepare_save(stored.principal, lease)
        peer.register(saving)
        peer.loss = loss
        result = dispatcher.step(stored.principal, lease, saving.effect.effect_id)
        assert result.operation.progress.state == 'uncertain'
        assert result.pause_reason == ('owner_protocol' if loss == 'malformed' else 'owner_unavailable')
        refresh.denied = True
        result = dispatcher.step(stored.principal, lease, saving.effect.effect_id)
        assert result.operation.progress.state == 'saved'
        assert peer.posts == [saving.request.canonical] and refresh.calls == 1


def test_denied_receipt_does_not_prove_absence(stored):
    with hosted(stored) as (_, journal, lease, dispatcher, refresh, peer):
        saving = journal.prepare_save(stored.principal, lease)
        peer.register(saving)
        peer.denied = True
        result = dispatcher.step(stored.principal, lease, saving.effect.effect_id)
        assert result.pause_reason == 'owner_access_denied'
        assert not peer.posts and not refresh.calls


def test_peer_commit_survives_local_fence_replacement(stored):
    with hosted(stored) as (store, journal, lease, dispatcher, refresh, peer):
        saving = journal.prepare_save(stored.principal, lease)
        peer.register(saving)
        successor = []
        def replace_lease():
            store.release(stored.principal, lease)
            successor.append(store.acquire(stored.principal, lease.selection.effect_id, seconds=300))
        peer.after_commit = replace_lease
        with pytest.raises(ValueError, match='compiler_lease_lost'):
            dispatcher.step(stored.principal, lease, saving.effect.effect_id)
        assert journal.read(stored.principal, lease.selection.effect_id, saving.effect.effect_id).progress.state == 'dispatching'
        refresh.denied = True
        recovered = dispatcher.step(stored.principal, successor[0], saving.effect.effect_id)
        assert recovered.operation.progress.state == 'saved' and len(peer.posts) == 1
        assert successor[0].fence > lease.fence and refresh.calls == 1


def test_cleanup_failure_propagates_without_reissuing_saved_command(stored, monkeypatch):
    with hosted(stored) as (store, journal, lease, dispatcher, _, peer):
        saving = journal.prepare_save(stored.principal, lease)
        peer.register(saving)
        store.release(stored.principal, lease)
        original_release = store.release
        def lost_cleanup_ack(principal, owned):
            original_release(principal, owned)
            raise ValueError('fixture_cleanup_ack_unknown')
        monkeypatch.setattr(store, 'release', lost_cleanup_ack)
        progression = CompilerProgression(dispatcher)
        with pytest.raises(ValueError, match='fixture_cleanup_ack_unknown'):
            progression.advance(stored.principal, lease.selection.effect_id)
        assert journal.read(stored.principal, lease.selection.effect_id, saving.effect.effect_id).progress.state == 'saved'
        monkeypatch.setattr(store, 'release', original_release)
        successor = store.acquire(stored.principal, lease.selection.effect_id, seconds=300)
        validating = journal.prepare_validation(stored.principal, successor)
        peer.register(validating)
        store.release(stored.principal, successor)
        result = progression.advance(stored.principal, lease.selection.effect_id)
        assert result.terminal and result.dispatch.operation.progress.state == 'compiled'
        assert peer.posts == [saving.request.canonical, validating.request.canonical]
