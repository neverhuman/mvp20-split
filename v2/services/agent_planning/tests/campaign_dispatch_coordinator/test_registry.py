"""Registry replay is effectful and fresh checks never rewrite an old round."""

import pytest

from .support import fixture

pytestmark = pytest.mark.postgres


def test_registry_candidate_enables_only_exact_fresh_runtime_preparation(stored):
    _, journal, lease, dispatcher, refresh, runtime, registry = fixture(stored, tools=True)
    first = journal.prepare_save(stored.principal, lease)
    result = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert result.pause_reason == 'dependency_unavailable' and not runtime.sent
    current = journal.prepare_round(stored.principal, lease, 'check-1')
    for check_id in ('absent', 'check-1'):
        incomplete = dispatcher.step(stored.principal, lease, first.effect.effect_id, check_id=check_id)
        assert incomplete.pause_reason == 'dependency_unavailable' and not runtime.sent
    candidate = dispatcher.step(stored.principal, lease, current.operations[0].effect.effect_id)
    assert candidate.operation.progress.state == 'candidate' and len(registry.sent) == 1
    result = dispatcher.step(stored.principal, lease, first.effect.effect_id, check_id='check-1')
    assert result.operation.progress.state == 'saved' and len(runtime.sent) == 1
    assert refresh.calls == 2


def test_registry_uncertainty_requires_fresh_rights_for_exact_replay(stored):
    _, journal, lease, dispatcher, refresh, _, registry = fixture(stored, tools=True)
    current = journal.prepare_round(stored.principal, lease, 'check-1')
    effect = current.operations[0].effect
    registry.lose_reply = True
    result = dispatcher.step(stored.principal, lease, effect.effect_id)
    assert result.operation.progress.state == 'uncertain' and len(registry.sent) == 1
    refresh.denied = True
    blocked = dispatcher.step(stored.principal, lease, effect.effect_id)
    assert blocked.pause_reason == 'input_unavailable' and len(registry.sent) == 1
    with pytest.raises(ValueError, match='compiler_round_unresolved'):
        journal.prepare_round(stored.principal, lease, 'new-identity')
    refresh.denied, registry.lose_reply = False, False
    recovered = dispatcher.step(stored.principal, lease, effect.effect_id)
    assert recovered.operation.progress.state == 'candidate'
    assert registry.sent == [effect.command().canonical_bytes] * 2
