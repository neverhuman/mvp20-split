"""Registry has no read-only receipt route; exact HTTP replay needs current use rights."""

import pytest

from .support import hosted

pytestmark = pytest.mark.postgres


def test_unknown_registry_commit_preserves_command_and_candidate_time(stored):
    with hosted(stored, tools=True) as (_, journal, lease, dispatcher, refresh, peer):
        batch = journal.prepare_round(stored.principal, lease, 'http-check-1')
        operation = batch.operations[0]
        peer.register(operation)
        peer.loss = 'disconnect'
        first = dispatcher.step(stored.principal, lease, operation.effect.effect_id)
        assert first.operation.progress.state == 'uncertain'
        original = peer.committed[operation.request.command.canonical_bytes]
        refresh.denied = True
        denied = dispatcher.step(stored.principal, lease, operation.effect.effect_id)
        assert denied.pause_reason == 'input_unavailable' and len(peer.posts) == 1
        refresh.denied, peer.loss = False, None
        recovered = dispatcher.step(stored.principal, lease, operation.effect.effect_id)
        assert recovered.operation.progress.state == 'candidate'
        assert peer.posts == [operation.request.command.canonical_bytes] * 2
        assert len(peer.registry.sent) == 1
        assert recovered.operation.progress.observation.outcome.receipt == original
        assert all(method == 'POST' for method, _, _ in peer.calls)
