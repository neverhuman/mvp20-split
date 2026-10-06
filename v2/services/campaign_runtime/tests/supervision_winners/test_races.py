"""Concurrent real-SQL contenders for a recipe-admitted immutable decision."""

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.supervision_winners import WinnerStore
from sqlalchemy import text

from ..supervision_resolution.support import record_response, save_report, setup


def contend(*operations):
    barrier = Barrier(len(operations))

    def run(operation):
        barrier.wait(timeout=10)
        return operation()

    with ThreadPoolExecutor(max_workers=len(operations)) as pool:
        futures = [pool.submit(run, operation) for operation in operations]
        return [future.result(timeout=30) for future in futures]


def assert_single_commit(graph, actor, ref, winner):
    assert WinnerStore(graph.env.engine).read(actor, ref) == winner
    with graph.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.supervision_winners WHERE run_id=:run'),
                            {'run': ref.run_id}).scalar_one() == 1
        assert conn.execute(text('SELECT count(*) FROM runtime.outbox WHERE operation_id=:operation'),
                            {'operation': winner.operation_id}).scalar_one() == 1
        assert conn.execute(text('SELECT count(*) FROM runtime.audit_events WHERE run_id=:run '
                                 "AND payload->>'decision_id'=:decision AND payload->>'kind'='supervision_checkpoint_decided'"),
                            {'run': ref.run_id, 'decision': ref.decision_id}).scalar_one() == 1
        assert conn.execute(text('SELECT count(*) FROM runtime.supervision_call_reservations WHERE run_id=:run'),
                            {'run': ref.run_id}).scalar_one() == 1


@pytest.mark.parametrize('cancel', [False, True])
def test_competing_responses_and_cancellation_commit_one_effect(graph_env, cancel):
    actor, ref, slot, preparer, original, resolver = setup(graph_env)
    responses = [record_response(actor, ref, slot, preparer, original, response_id=name)
                 for name in ('contender-a', 'contender-b')]
    save_report(resolver, actor, original, responses[0])
    store = WinnerStore(graph_env.env.engine)
    operations = [lambda response=response: store.resolve(actor, ref, response_id=response.response_id)
                  for response in responses]
    if cancel:
        command = graph_env.command('runtime.cancel', {'run_id': ref.run_id, 'reason_code': 'race_probe'})
        operations.append(lambda: AuthorityCommands(graph_env.env.engine).cancel(actor, command))
    results = contend(*operations)
    winner = results[0]
    assert winner == results[1]
    assert winner.document().outcome.kind in ({'model_accepted', 'cancelled'} if cancel else {'model_accepted'})
    assert (winner.selection is not None) == (winner.document().outcome.kind == 'model_accepted')
    assert store.resolve(actor, ref, response_id='unrecorded-late-response') == winner
    assert_single_commit(graph_env, actor, ref, winner)


def test_deadline_fallback_and_late_model_contend_without_scalar_effect(graph_env):
    actor, ref, slot, preparer, original, resolver = setup(graph_env, timeout=8)
    response = record_response(actor, ref, slot, preparer, original)
    save_report(resolver, actor, original, response)
    with graph_env.env.engine.connect() as conn:
        remaining = (slot.deadline - conn.execute(text('SELECT clock_timestamp()')).scalar_one()).total_seconds()
    assert remaining > 0, 'Fixture setup must retain time before the original deadline'
    time.sleep(remaining + 0.03)
    store = WinnerStore(graph_env.env.engine)
    winners = contend(lambda: store.resolve(actor, ref),
                      lambda: store.resolve(actor, ref, response_id=response.response_id))
    assert winners[0] == winners[1]
    assert winners[0].document().outcome.reason_code == 'checkpoint_deadline_exhausted'
    assert winners[0].selection is None
    assert_single_commit(graph_env, actor, ref, winners[0])


def test_withdrawn_acceptance_authority_cannot_join_winner_race(graph_env):
    actor, ref, slot, preparer, original, resolver = setup(graph_env)
    response = record_response(actor, ref, slot, preparer, original)
    save_report(resolver, actor, original, response)
    store = WinnerStore(graph_env.env.engine)

    def unauthorized():
        with pytest.raises(ValueError):
            store.resolve(replace(actor, actions=frozenset({'read'})), ref, response_id=response.response_id)

    winner, _ = contend(lambda: store.resolve(actor, ref, response_id=response.response_id), unauthorized)
    assert winner.document().outcome.kind == 'model_accepted'
    assert_single_commit(graph_env, actor, ref, winner)
