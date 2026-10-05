"""Bounded owned progression composes checks/save/validation without activation."""

import pytest
from amphora_agent_planning.campaign_dispatch.progression import CompilerProgression

from .support import fixture

pytestmark = pytest.mark.postgres


def setup(stored, *, tools=False):
    store, journal, lease, dispatcher, refresh, runtime, registry = fixture(stored, tools=tools, maximum_age_seconds=60)
    store.release(stored.principal, lease)
    return CompilerProgression(dispatcher), lease.selection.effect_id, journal, refresh, runtime, registry


@pytest.mark.parametrize('valid', [True, False])
def test_zero_tool_save_validate_and_terminal_replay(stored, valid):
    owner, identity, journal, _, runtime, _ = setup(stored)
    assert journal.latest_round(stored.principal, identity) is None
    assert journal.latest_round(stored.principal, 'absent-selection') is None
    first = owner.advance(stored.principal, identity)
    assert first.stage == 'save' and not first.terminal and first.dispatch.operation.progress.state == 'saved'
    runtime.valid = valid
    second = owner.advance(stored.principal, identity)
    assert second.stage == 'validation' and second.terminal
    assert second.dispatch.operation.progress.state == ('compiled' if valid else 'structural_invalid')
    replay = owner.advance(stored.principal, identity)
    assert replay.dispatch.operation == second.dispatch.operation and len(runtime.sent) == 2
    assert journal.latest_round(stored.principal, identity) is None


def test_tool_round_precedes_save_validate_and_lease_is_released(stored):
    owner, identity, journal, _, runtime, registry = setup(stored, tools=True)
    checked = owner.advance(stored.principal, identity)
    assert checked.stage == 'eligibility' and not checked.terminal and checked.round.terminal
    assert checked.round.check_id == 'planning-check-1' and checked.round.next_operation is None
    assert len(registry.sent) == 1 and not runtime.sent
    saved = owner.advance(stored.principal, identity)
    assert saved.stage == 'save' and saved.dispatch.operation.progress.state == 'saved'
    compiled = owner.advance(stored.principal, identity)
    assert compiled.terminal and compiled.dispatch.operation.progress.state == 'compiled'
    assert journal.latest_round(stored.principal, identity) == checked.round
    assert len(runtime.sent) == 2 and len(registry.sent) == 1
    lease = owner.store.acquire(stored.principal, identity)
    owner.store.release(stored.principal, lease)


def test_unknown_registry_result_keeps_original_round_and_command(stored):
    owner, identity, journal, _, runtime, registry = setup(stored, tools=True)
    registry.lose_reply = True
    first = owner.advance(stored.principal, identity)
    assert first.pause_reason == 'owner_unavailable' and first.round.ordinal == 1
    assert not first.round.terminal and first.round.next_operation is not None
    registry.lose_reply = False
    second = owner.advance(stored.principal, identity)
    assert second.round.ordinal == 1 and second.round.terminal and not runtime.sent
    assert registry.sent[0] == registry.sent[1]
    assert journal.latest_round(stored.principal, identity) == second.round
