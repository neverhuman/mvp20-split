"""Pending owner commands and relevant changes remain explicit bounded outcomes."""

from dataclasses import replace

import pytest
from amphora_agent_planning.campaign_authoring import AuthoringOutcome
from amphora_agent_planning.campaign_refresh import RefreshChange

from ..campaign_authoring.test_values import receipt
from ..campaign_dispatch_storage.test_journal import observed
from .support import fixture

pytestmark = pytest.mark.postgres


def test_pending_observation_reuse_and_pending_post_are_not_success(stored, monkeypatch):
    _, journal, lease, dispatcher, refresh, runtime, _ = fixture(stored)
    first = journal.prepare_save(stored.principal, lease)
    pending = AuthoringOutcome.bind(first.request, receipt(first.request, 'pending'))
    runtime.outcomes[first.request.canonical] = pending
    recorded = observed(journal, stored.principal, lease, first, pending.receipt)
    refresh.denied = True
    blocked = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert blocked.operation.progress.position == recorded.progress.position + 1
    assert not runtime.sent
    def submit(request, window, *, guard):
        guard()
        runtime.sent.append(request.canonical)
        return pending
    monkeypatch.setattr(runtime, 'submit', submit)
    refresh.denied = False
    result = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert result.operation.progress.state == 'pending' and not result.operation.terminal
    assert runtime.sent == [first.request.canonical]


@pytest.mark.parametrize('tools', [False, True])
def test_relevant_change_blocks_new_runtime_and_registry_effects(stored, monkeypatch, tools):
    _, journal, lease, dispatcher, refresh, runtime, registry = fixture(stored, tools=tools)
    first = (journal.prepare_round(stored.principal, lease, 'check-1').operations[0] if tools
             else journal.prepare_save(stored.principal, lease))
    original = refresh.collect
    def changed(plan):
        result = original(plan)
        key = next(iter(plan.review.read_set.keys))
        return replace(result, changes=(RefreshChange(key, 'a' * 64, 'b' * 64),))
    monkeypatch.setattr(refresh, 'collect', changed)
    result = dispatcher.step(stored.principal, lease, first.effect.effect_id)
    assert result.pause_reason == 'relevant_input_changed' and not runtime.sent and not registry.sent
