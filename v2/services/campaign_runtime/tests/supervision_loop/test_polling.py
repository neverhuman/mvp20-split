"""SQL discovery is scoped, restartable and fair while original owners remain authoritative."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.supervision_loop import LoopStep
from amphora_campaign_runtime.supervision_loop.polling import CheckpointPoller
from sqlalchemy import text

from .support import fixture


def test_discovers_and_finishes_original_without_manual_request_id(graph_env):
    actor, ref, _, loop, peer, _ = fixture(graph_env)
    poller = CheckpointPoller(graph_env.env.engine, loop)
    assert poller.tick(actor).stage == 'prepared'
    # A replacement starts from owned facts, not an in-memory queue or new request.
    poller = CheckpointPoller(graph_env.env.engine, loop)
    assert [poller.tick(actor).stage for _ in range(4)] == ['delivery', 'delivery', 'report_recorded', 'decided']
    assert poller.tick(actor) is None
    assert len(loop.preparer.journal.series(actor, ref.run_id, ref.decision_id)) == 1
    assert peer.calls.count('submit') == 1


def test_foreign_actor_and_scope_cannot_discover_original_work(graph_env):
    actor, _, _, loop, _, _ = fixture(graph_env, prepare=True)
    poller = CheckpointPoller(graph_env.env.engine, loop)
    assert poller.tick(replace(actor, actor_id='foreign')) is None
    foreign_scope = actor.scope.model_copy(update={'project_id': 'foreign-project'})
    assert poller.tick(replace(actor, scope=foreign_scope)) is None
    with pytest.raises(ValueError):
        poller.tick(replace(actor, actions=frozenset({'read'})))


def test_fairness_wraps_pending_slots_and_includes_cancelled_runs(graph_env):
    initial_entry = graph_env.entry
    actor, first, _, loop, _, _ = fixture(graph_env)
    with graph_env.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE run_id=:run"), {'run': first.run_id})
    graph_env.entry = initial_entry
    _, second, _, _, _, _ = fixture(graph_env)
    seen = []
    def pending(principal, reference):
        seen.append(reference)
        return LoopStep('pending')
    poller = CheckpointPoller(graph_env.env.engine, SimpleNamespace(tick=pending))
    for _ in range(4):
        poller.tick(actor)
    assert {item.run_id for item in seen[:2]} == {first.run_id, second.run_id}
    assert seen[:2] == seen[2:]
    assert loop.tick(actor, first).winner.document().outcome.kind == 'cancelled'


@pytest.mark.parametrize('seconds,interval', [(0, 1), (float('nan'), 1), (1, float('inf')), (True, 1)])
def test_invalid_sweep_window_rejects_without_database(seconds, interval):
    with pytest.raises(ValueError, match='checkpoint_polling_window'):
        CheckpointPoller(None, None).sweep(None, seconds=seconds, interval=interval)


def test_bounded_sweep_counts_idle_and_stages(monkeypatch):
    import amphora_campaign_runtime.supervision_loop.polling as module
    clock = iter([0, 0, .1, .2, .3, 1])
    monkeypatch.setattr(module.time, 'monotonic', lambda: next(clock))
    monkeypatch.setattr(module.time, 'sleep', lambda _: None)
    results = iter([None, LoopStep('pending')])
    poller = CheckpointPoller(None, None)
    monkeypatch.setattr(poller, 'tick', lambda _: next(results))
    assert poller.sweep(None, seconds=1) == {'idle': 1, 'pending': 1}
