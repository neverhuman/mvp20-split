"""Actual SQL winners, rollback and authority fences; no coordinator release yet."""

import time
from dataclasses import replace

import pytest
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.supervision_winners import WinnerStore
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..supervision_checkpoints.test_values import binding
from .support import prepare, setup


def test_model_winner_is_atomic_immutable_and_replayed_after_cancellation(graph_env):
    store, actor, ref, slot = setup(graph_env)
    assert store.resolve(actor, ref) is None
    response = prepare(graph_env, actor, ref, slot)
    result = store.resolve(actor, ref, response_id=response)
    assert result.document().outcome.kind == 'model_accepted'
    assert result.selection.resolve((binding(),)) == (binding(2),)
    assert WinnerStore(graph_env.env.engine).read(actor, ref) == result
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.outbox WHERE operation_id=:operation'),
            {'operation': result.operation_id}).scalar_one() == 1
        assert conn.execute(text('SELECT count(*) FROM runtime.binding_intents WHERE run_id=:run'),
            {'run': ref.run_id}).scalar_one() == 0
    AuthorityCommands(graph_env.env.engine).cancel(actor, graph_env.command('runtime.cancel', {'run_id': ref.run_id, 'reason_code': 'fixture_done'}))
    assert store.resolve(actor, ref, response_id='late-other-response') == result
    with pytest.raises(DBAPIError), graph_env.env.engine.begin() as conn:
        conn.execute(text('DELETE FROM runtime.supervision_winners WHERE run_id=:run'), {'run': ref.run_id})


@pytest.mark.parametrize('fallback', ['continue_unchanged', 'block_target'])
def test_expired_slot_fallback_needs_no_request(graph_env, fallback):
    store, actor, ref, slot = setup(graph_env, timeout=1, fallback=fallback)
    time.sleep(max(0, slot.deadline.timestamp() - time.time()) + 0.02)
    winner = store.resolve(actor, ref)
    assert winner.document().outcome.kind == 'fallback'
    assert winner.document().outcome.action == fallback
    assert winner.selection is None
    assert store.resolve(actor, ref) == winner


def test_cancellation_beats_unaccepted_model_response(graph_env):
    store, actor, ref, slot = setup(graph_env)
    response = prepare(graph_env, actor, ref, slot)
    AuthorityCommands(graph_env.env.engine).cancel(actor, graph_env.command('runtime.cancel', {'run_id': ref.run_id, 'reason_code': 'fixture_done'}))
    winner = store.resolve(actor, ref, response_id=response)
    assert winner.document().outcome.kind == 'cancelled'
    assert winner.selection is None


def test_winner_audit_effect_and_revision_rollback_together(graph_env, monkeypatch):
    store, actor, ref, slot = setup(graph_env)
    response = prepare(graph_env, actor, ref, slot)
    commit = store._commit
    def fail(*args):
        commit(*args)
        raise RuntimeError('after-winner-before-commit')
    monkeypatch.setattr(store, '_commit', fail)
    with pytest.raises(RuntimeError, match='after-winner-before-commit'):
        store.resolve(actor, ref, response_id=response)
    assert store.read(actor, ref) is None
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT revision FROM runtime.runs WHERE run_id=:run'), {'run': ref.run_id}).scalar_one() == 0
        assert conn.execute(text("SELECT count(*) FROM runtime.outbox WHERE operation_id LIKE :operation"),
            {'operation': 'checkpoint:' + ref.decision_id}).scalar_one() == 0
    monkeypatch.setattr(store, '_commit', commit)
    assert store.resolve(actor, ref, response_id=response).document().outcome.kind == 'model_accepted'


def test_invalid_proposal_does_not_steal_slot_or_rewrite_response(graph_env):
    store, actor, ref, slot = setup(graph_env)
    response = prepare(graph_env, actor, ref, slot,
        mutation=lambda draft: draft['candidate']['changes'][0]['proposed'].update(value=11))
    with pytest.raises(ValueError, match='scalar_adjustment_outside_policy'):
        store.resolve(actor, ref, response_id=response)
    assert store.read(actor, ref) is None


def test_acceptance_requires_owner_action_and_exact_scope(graph_env):
    store, actor, ref, _ = setup(graph_env)
    with pytest.raises(ValueError):
        store.resolve(replace(actor, actions=frozenset({'read'})), ref)
    with pytest.raises(ValueError, match='winner_scope_mismatch'):
        store.read(actor, ref.model_copy(update={'scope': ref.scope.model_copy(update={'project_id': 'foreign'})}))


def test_review_only_invoke_can_fallback_without_scalar_fields(graph_env):
    store, actor, ref, slot = setup(graph_env, invoke=True, timeout=1)
    time.sleep(max(0, slot.deadline.timestamp() - time.time()) + 0.02)
    winner = store.resolve(actor, ref)
    assert winner.document().outcome.kind == 'fallback' and winner.selection is None


def test_abstention_retains_proposal_without_inventing_effect(graph_env):
    store, actor, ref, slot = setup(graph_env)
    response = prepare(graph_env, actor, ref, slot,
        mutation=lambda draft: draft.update(action='abstain', candidate=None))
    winner = store.resolve(actor, ref, response_id=response)
    assert winner.document().outcome.effect.kind == 'abstained'
    assert winner.selection is None
    assert store.read(actor, ref) == winner


def test_selected_progress_rejects_model_without_terminalizing_slot(graph_env):
    store, actor, ref, slot = setup(graph_env)
    response = prepare(graph_env, actor, ref, slot)
    with graph_env.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.graph_nodes SET state=CAST(:state AS jsonb) WHERE run_id=:run AND node_id='pack'"),
                     {'run': ref.run_id, 'state': '{"changed":true}'})
    with pytest.raises(ValueError, match='selected_observation_changed'):
        store.resolve(actor, ref, response_id=response)
    assert store.read(actor, ref) is None


@pytest.mark.parametrize('case,reason', [('policy', 'winner_request_policy'), ('calls', 'winner_request_ceiling')])
def test_recorded_request_cannot_expand_admitted_authority(graph_env, case, reason):
    store, actor, ref, slot = setup(graph_env)
    def mutate(data):
        if case == 'policy':
            data['policy']['sha256'] = 'e' * 64
        else:
            data['planning_request']['context']['limits']['max_attempts'] = 5
    response = prepare(graph_env, actor, ref, slot, request_mutation=mutate)
    with pytest.raises(ValueError, match=reason):
        store.resolve(actor, ref, response_id=response)
    assert store.read(actor, ref) is None


def test_future_topology_is_retained_without_mutating_current_plan(graph_env):
    store, actor, ref, slot = setup(graph_env)
    def future(draft):
        draft['candidate'] = {'kind': 'future_campaign', 'title': 'Later synthetic experiment',
            'definition': slot.seed.policy.plan.document.definition.model_dump(mode='json'), 'expected_evidence': []}
    response = prepare(graph_env, actor, ref, slot, mutation=future)
    winner = store.resolve(actor, ref, response_id=response)
    assert winner.document().outcome.effect.kind == 'future_campaign' and winner.selection is None
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT plan_sha256 FROM runtime.graph_runs WHERE run_id=:run'),
            {'run': ref.run_id}).scalar_one() == slot.seed.policy.plan.sha256


def test_expired_model_cannot_replace_fallback(graph_env):
    store, actor, ref, slot = setup(graph_env, timeout=3)
    response = prepare(graph_env, actor, ref, slot)
    time.sleep(max(0, slot.deadline.timestamp() - time.time()) + 0.02)
    first = store.resolve(actor, ref, response_id=response)
    assert first.document().outcome.kind == 'fallback' and first.selection is None
    assert store.resolve(actor, ref, response_id=response) == first
