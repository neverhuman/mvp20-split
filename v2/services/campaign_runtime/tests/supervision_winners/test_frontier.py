"""Actual frontier release requires a committed winner and never bypasses scalar integration."""

import time

from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from sqlalchemy import text

from .support import prepare, setup


def advance(graph, ref):
    return GraphAdvancer(graph.env.engine).advance(graph.env.principal,
        graph.command('graph.advance', {'run_id': ref.run_id}))


def test_pending_then_unchanged_invoke_releases_once(graph_env):
    store, actor, ref, slot = setup(graph_env, invoke=True, timeout=1)
    assert advance(graph_env, ref).outcome.status == 'accepted'
    time.sleep(max(0, slot.deadline.timestamp() - time.time()) + 0.02)
    store.resolve(actor, ref)
    for _ in range(2):
        assert advance(graph_env, ref).outcome.status == 'accepted'
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.activations WHERE run_id=:run'),
            {'run': ref.run_id}).scalar_one() == 1
        assert conn.execute(text("SELECT status FROM runtime.graph_nodes WHERE run_id=:run AND kind='invoke'"),
            {'run': ref.run_id}).scalar_one() == 'issued'


def test_pinned_block_fallback_never_issues_tool(graph_env):
    store, actor, ref, slot = setup(graph_env, invoke=True, timeout=1, fallback='block_target')
    time.sleep(max(0, slot.deadline.timestamp() - time.time()) + 0.02)
    store.resolve(actor, ref)
    assert advance(graph_env, ref).outcome.status == 'accepted'
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.activations WHERE run_id=:run'),
            {'run': ref.run_id}).scalar_one() == 0
        row = conn.execute(text("SELECT status,reason_code FROM runtime.graph_nodes WHERE run_id=:run AND kind='invoke'"),
            {'run': ref.run_id}).one()
        assert row.status == 'blocked' and row.reason_code == 'checkpoint_deadline_exhausted'


def test_committed_review_outcome_releases_invoke_without_scalar_input_change(graph_env):
    store, actor, ref, slot = setup(graph_env, invoke=True)
    response = prepare(graph_env, actor, ref, slot,
        mutation=lambda draft: draft.update(action='abstain', candidate=None),
        request_mutation=lambda data: data['planning_request']['context']['limits'].update(max_attempts=1))
    assert store.resolve(actor, ref, response_id=response).document().outcome.effect.kind == 'abstained'
    assert advance(graph_env, ref).outcome.status == 'accepted'
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.activations WHERE run_id=:run'),
            {'run': ref.run_id}).scalar_one() == 1
