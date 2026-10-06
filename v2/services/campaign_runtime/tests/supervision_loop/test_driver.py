"""Bounded ticks preserve original requests, failures, repair context and winners."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from amphora_campaign_runtime.coordinator.projections import ProjectionUnavailable
from amphora_campaign_runtime.supervision_client import (
    ExchangeAbsent,
    ExchangeUnavailable,
)
from amphora_campaign_runtime.supervision_context.preparation import ContextPreparer
from amphora_campaign_runtime.supervision_loop import CheckpointLoop
from amphora_contracts_supervision import CheckpointRepairContext
from sqlalchemy import text

from ..supervision_resolution.support import record_response, save_report
from .support import fixture


def test_initial_delivery_report_fallback_and_replay_are_separate_ticks(graph_env):
    actor, ref, _, loop, peer, _ = fixture(graph_env)
    assert loop.tick(actor, ref).stage == 'prepared'
    assert peer.calls == []
    assert loop.tick(actor, ref).stage == 'delivery'
    assert loop.tick(actor, ref).stage == 'delivery'
    assert loop.tick(actor, ref).stage == 'report_recorded'
    result = loop.tick(actor, ref)
    assert result.terminal and result.winner.document().outcome.reason_code == 'checkpoint_provider_unconfigured'
    before = list(peer.calls)
    replacement = CheckpointLoop(loop.preparer, None, None, loop.resolver)
    assert replacement.tick(actor, ref).winner == result.winner
    assert peer.calls == before


@pytest.mark.parametrize('error', [ExchangeAbsent('fixture_absent'), ExchangeUnavailable('fixture_uncertain')])
def test_report_uncertainty_never_creates_successor_or_paid_attempt(graph_env, error):
    actor, ref, _, loop, peer, original = fixture(graph_env, prepare=True)
    loop.tick(actor, ref)
    loop.tick(actor, ref)
    peer.report_error = error
    assert loop.tick(actor, ref).reason == 'execution_report_unresolved'
    assert loop.resolver.winners.read(actor, ref) is None
    assert loop.preparer.journal.series(actor, ref.run_id, ref.decision_id) == (original,)


def test_rejected_delivery_uses_owned_terminal_evidence(graph_env):
    actor, ref, _, loop, peer, original = fixture(graph_env, prepare=True)
    assert loop.fallback.resolve(actor, ref, delivery_request=original.frame.request_sha256) is None
    peer.rejected = True
    assert loop.tick(actor, ref).stage == 'delivery'
    result = loop.tick(actor, ref)
    assert result.winner.document().outcome.reason_code == 'checkpoint_delivery_rejected'
    assert 'execution' not in peer.calls


def test_repair_context_created_once_and_stale_failure_cannot_override_child(graph_env):
    actor, ref, slot, loop, _, original = fixture(graph_env, prepare=True)
    loop.tick(actor, ref)
    loop.tick(actor, ref)
    response = record_response(actor, ref, slot, loop.preparer, original, variant='invalid')
    save_report(loop.resolver, actor, original, response)
    # Another worker legitimately owns the run lock during this concurrency probe.
    # The single-worker publication tests retain the independent NOWAIT check.
    loop.preparer.publisher.artifacts.check_unlocked = False
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: loop.tick(actor, ref), range(2)))
    children = loop.preparer.journal.series(actor, ref.run_id, ref.decision_id)
    assert len(children) == 2
    assert all(item.stage in {'prepared', 'delivery'} for item in results)
    child = children[-1]
    artifact = child.frame.request.planning_request.context.entries[-1].artifact
    declaration = CheckpointRepairContext.model_validate_json(loop.preparer.publisher.artifacts.documents[artifact.artifact_id])
    assert declaration.repair.parent_request_sha256 == original.frame.request_sha256
    assert loop.fallback.resolve(actor, ref, parent=original.frame.request_sha256,
        preparation_reason='binding_publication_rejected') is None
    assert child.frame.request.deadline_unix_ms == original.frame.request.deadline_unix_ms


def test_exact_capture_pending_then_acceptance_without_another_peer_call(graph_env):
    actor, ref, slot, loop, peer, original = fixture(graph_env, prepare=True)
    loop.tick(actor, ref)
    loop.tick(actor, ref)
    response = record_response(actor, ref, slot, loop.preparer, original, record=False)
    save_report(loop.resolver, actor, original, response)
    assert loop.tick(actor, ref).stage == 'pending'
    before = list(peer.calls)
    record_response(actor, ref, slot, loop.preparer, original)
    result = loop.tick(actor, ref)
    assert result.winner.document().outcome.kind == 'model_accepted'
    assert peer.calls == before


def test_fallback_rechecks_allowance_fields_and_original_winner(graph_env):
    actor, ref, _, loop, _, _ = fixture(graph_env)
    for reason in ('context_allowance_exhausted', 'context_original_fields_changed'):
        assert loop.fallback.resolve(actor, ref, preparation_reason=reason) is None
    winner = loop.fallback.resolve(actor, ref, preparation_reason='binding_publication_rejected')
    assert loop.fallback.resolve(actor, ref, preparation_reason='context_allowance_exhausted') == winner


def test_repair_fallback_requires_durable_intent(graph_env):
    actor, ref, slot, loop, _, original = fixture(graph_env, prepare=True)
    sha = original.frame.request_sha256
    with pytest.raises(ValueError, match='loop_repair_intent_required'):
        loop.fallback.resolve(actor, ref, parent=sha, preparation_reason='binding_publication_rejected')
    response = record_response(actor, ref, slot, loop.preparer, original, variant='invalid')
    save_report(loop.resolver, actor, original, response)
    loop.resolver.resolve(actor, ref, sha)
    winner = loop.fallback.resolve(actor, ref, parent=sha, preparation_reason='binding_publication_rejected')
    assert winner.document().outcome.kind == 'fallback'


def test_changed_selected_facts_request_refresh_without_fabricated_failure(graph_env, monkeypatch):
    actor, ref, _, loop, _, _ = fixture(graph_env)
    def changed(*args, **kwargs):
        raise ValueError('selected_observation_changed')
    monkeypatch.setattr(loop.preparer, 'prepare', changed)
    assert loop.tick(actor, ref).reason == 'selected_observation_changed'
    assert loop.resolver.winners.read(actor, ref) is None


@pytest.mark.parametrize('error,terminal', [(ProjectionUnavailable('uncertain'), False),
                                           (ValueError('binding_publication_rejected'), True)])
def test_preparation_failure_is_not_a_model_observation(graph_env, monkeypatch, error, terminal):
    actor, ref, _, loop, _, _ = fixture(graph_env)
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(loop.preparer.publisher.artifacts, 'publish', fail)
    result = loop.tick(actor, ref)
    assert result.terminal is terminal
    assert loop.preparer.journal.series(actor, ref.run_id, ref.decision_id) == ()
    with graph_env.env.engine.connect() as conn:
        for table in ('supervision_responses', 'supervision_call_reservations', 'supervision_execution_reports'):
            assert conn.execute(text(f'SELECT count(*) FROM runtime.{table} WHERE run_id=:run'),
                                {'run': ref.run_id}).scalar_one() == 0


def test_missing_delegation_falls_back_but_fixed_configuration_does_not(graph_env):
    actor, ref, _, loop, _, _ = fixture(graph_env)
    assert loop.fallback.resolve(actor, ref, preparation_reason='planning_delegation_unavailable') is None
    loop.preparer = ContextPreparer(graph_env.env.engine, {}, loop.preparer.publisher.artifacts)
    loop = CheckpointLoop(loop.preparer, loop.dispatcher, loop.collector, loop.resolver)
    result = loop.tick(actor, ref)
    assert result.winner.document().outcome.reason_code == 'checkpoint_planning_delegation_unavailable'


def test_unexpected_integrity_errors_propagate(graph_env, monkeypatch):
    actor, ref, _, loop, _, _ = fixture(graph_env)
    def fail(*args, **kwargs):
        raise ValueError('stored_fixture_integrity')
    monkeypatch.setattr(loop.preparer.publisher.artifacts, 'publish', fail)
    with pytest.raises(ValueError, match='stored_fixture_integrity'):
        loop.tick(actor, ref)
    assert loop.resolver.winners.read(actor, ref) is None


def test_cancelled_run_precedes_any_publication(graph_env):
    actor, ref, _, loop, peer, _ = fixture(graph_env)
    with graph_env.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE run_id=:run"), {'run': ref.run_id})
    result = loop.tick(actor, ref)
    assert result.winner.document().outcome.kind == 'cancelled'
    assert not peer.calls and not loop.preparer.publisher.artifacts.calls
