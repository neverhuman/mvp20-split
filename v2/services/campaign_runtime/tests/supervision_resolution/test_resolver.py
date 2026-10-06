"""Run-locked owner evidence produces one winner or a durable bounded repair intent."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from amphora_campaign_runtime.supervision_resolution import OutcomeResolver
from amphora_campaign_runtime.supervision_resolution.disposition import (
    RequestDisposition,
)
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .support import record_response, save_report, setup


def test_pre_call_failure_selects_pinned_fallback_without_observation(graph_env):
    actor, ref, _, _, original, resolver = setup(graph_env)
    sha = original.frame.request_sha256
    assert resolver.resolve(actor, ref, sha) is None
    save_report(resolver, actor, original)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(resolver.resolve, actor, ref, sha) for _ in range(2)]
        first, second = (item.result(30) for item in futures)
    assert first == second and first.document().outcome.kind == 'fallback'
    assert first.document().outcome.reason_code == 'checkpoint_provider_unconfigured'
    assert first.document().outcome.action == 'continue_unchanged'
    assert OutcomeResolver(resolver.reports).resolve(actor, ref, sha) == first
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.supervision_responses WHERE run_id=:run'),
            {'run': ref.run_id}).scalar_one() == 0
    with pytest.raises(DBAPIError), graph_env.env.engine.begin() as conn:
        conn.execute(text('DELETE FROM runtime.supervision_request_dispositions WHERE run_id=:run'), {'run': ref.run_id})


def test_valid_response_is_accepted_through_existing_winner(graph_env):
    actor, ref, slot, preparer, original, resolver = setup(graph_env)
    response = record_response(actor, ref, slot, preparer, original)
    save_report(resolver, actor, original, response)
    winner = resolver.resolve(actor, ref, original.frame.request_sha256)
    assert winner.document().outcome.kind == 'model_accepted'
    assert winner.selection.document().changes[0].value.value == 2


def test_report_waits_for_exact_capture_and_skips_late_different_observation(graph_env):
    actor, ref, slot, preparer, original, resolver = setup(graph_env)
    primary = record_response(actor, ref, slot, preparer, original, variant='invalid', record=False)
    save_report(resolver, actor, original, primary)
    assert resolver.resolve(actor, ref, original.frame.request_sha256) is None
    record_response(actor, ref, slot, preparer, original, response_id='late-different')
    assert resolver.resolve(actor, ref, original.frame.request_sha256) is None
    record_response(actor, ref, slot, preparer, original, variant='invalid')
    assert resolver.resolve(actor, ref, original.frame.request_sha256).document().kind == 'repair'


@pytest.mark.parametrize('variant,reason', [('invalid', 'checkpoint_output_rejected'),
                                          ('outside', 'scalar_adjustment_outside_policy')])
def test_failed_output_records_repair_without_issuing_successor(graph_env, variant, reason):
    actor, ref, slot, preparer, original, resolver = setup(graph_env)
    response = record_response(actor, ref, slot, preparer, original, variant=variant)
    save_report(resolver, actor, original, response)
    result = resolver.resolve(actor, ref, original.frame.request_sha256)
    assert isinstance(result, RequestDisposition)
    assert result.document().kind == 'repair' and result.document().reason_code == reason
    assert result.document().response_id == response.response_id
    assert resolver.resolve(actor, ref, original.frame.request_sha256) == result
    assert len(preparer.journal.series(actor, ref.run_id, ref.decision_id)) == 1
    assert resolver.winners.read(actor, ref) is None


def test_exhausted_actual_reservation_chooses_fallback(graph_env):
    actor, ref, slot, preparer, original, resolver = setup(graph_env, calls=1)
    response = record_response(actor, ref, slot, preparer, original, variant='invalid')
    save_report(resolver, actor, original, response)
    winner = resolver.resolve(actor, ref, original.frame.request_sha256)
    assert winner.document().outcome.kind == 'fallback'
    assert winner.document().outcome.reason_code == 'checkpoint_request_allowance_exhausted'


def test_late_response_cannot_replace_reported_observation_or_superseded_request(graph_env):
    actor, ref, slot, preparer, original, resolver = setup(graph_env)
    primary = record_response(actor, ref, slot, preparer, original, variant='invalid')
    save_report(resolver, actor, original, primary)
    late = record_response(actor, ref, slot, preparer, original, response_id='late-valid')
    with pytest.raises(ValueError, match='execution_response_observation'):
        resolver.winners.resolve(actor, ref, response_id=late.response_id)
    repair = resolver.resolve(actor, ref, original.frame.request_sha256)
    assert repair.document().kind == 'repair'
    preparer.prepare(actor, ref, parent_request_sha256=original.frame.request_sha256)
    with pytest.raises(ValueError, match='winner_request_superseded'):
        resolver.winners.resolve(actor, ref, response_id=late.response_id)
    assert resolver.resolve(actor, ref, original.frame.request_sha256) == repair


def test_disposition_and_winner_rollback_together(graph_env, monkeypatch):
    actor, ref, _, _, original, resolver = setup(graph_env)
    save_report(resolver, actor, original)
    commit = resolver.winners._commit
    def fail(*args):
        commit(*args)
        raise RuntimeError('fixture-after-write')
    monkeypatch.setattr(resolver.winners, '_commit', fail)
    with pytest.raises(RuntimeError, match='fixture-after-write'):
        resolver.resolve(actor, ref, original.frame.request_sha256)
    assert resolver.winners.read(actor, ref) is None
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.supervision_request_dispositions WHERE run_id=:run'),
                            {'run': ref.run_id}).scalar_one() == 0
    monkeypatch.setattr(resolver.winners, '_commit', commit)
    assert resolver.resolve(actor, ref, original.frame.request_sha256).document().outcome.kind == 'fallback'


def test_incompatible_provider_profile_falls_back_instead_of_repeating_calls(graph_env):
    actor, ref, slot, preparer, original, resolver = setup(graph_env)
    response = record_response(actor, ref, slot, preparer, original, variant='profile')
    saved = save_report(resolver, actor, original, response)
    winner = resolver.resolve(actor, ref, original.frame.request_sha256)
    assert winner.document().outcome.reason_code == 'checkpoint_provider_profile_unavailable'
    assert len(preparer.journal.series(actor, ref.run_id, ref.decision_id)) == 1
    params = resolver.reports.params(actor, ref, original.frame.request_sha256)
    with graph_env.env.engine.connect() as conn:
        row = conn.execute(text('SELECT * FROM runtime.supervision_request_dispositions WHERE run_id=:run'),
                           params).mappings().one()
        restored = RequestDisposition.restore(row, saved.report, resolver.responses(conn, params))
    assert restored.document().kind == 'fallback'


def test_missing_success_capture_waits_and_unexpected_failure_is_not_model_repair(graph_env, monkeypatch):
    actor, ref, slot, preparer, original, resolver = setup(graph_env)
    response = record_response(actor, ref, slot, preparer, original, record=False)
    save_report(resolver, actor, original, response)
    assert resolver.resolve(actor, ref, original.frame.request_sha256) is None
    record_response(actor, ref, slot, preparer, original)
    resolve = resolver.winners.resolve_locked
    def unexpected(*args, **kwargs):
        if kwargs.get('response_id') is not None:
            raise ValueError('fixture_internal_corruption')
        return resolve(*args, **kwargs)
    monkeypatch.setattr(resolver.winners, 'resolve_locked', unexpected)
    with pytest.raises(ValueError, match='fixture_internal_corruption'):
        resolver.resolve(actor, ref, original.frame.request_sha256)
    assert resolver.winners.read(actor, ref) is None
    with graph_env.env.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM runtime.supervision_request_dispositions WHERE run_id=:run'),
                            {'run': ref.run_id}).scalar_one() == 0
