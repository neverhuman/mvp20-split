"""Actual Planning persistence, immutable reports and new-issuance closure."""

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Event

import pytest
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.providers.capture import (
    CapturedOutput,
    Observation,
    unknown_usage,
)
from amphora_agent_planning.supervision_completion import CompletionJournal
from amphora_agent_planning.supervision_execution.worker import CheckpointWorker
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..supervision_api.test_http import FOREIGN, READ, client
from ..supervision_execution.test_worker import setup


def test_pre_call_failure_is_immutable_replay_and_never_charges(stored):
    worker, data, provider, intake = setup(stored)
    engagement = intake.planning.document().reference.engagement_id
    worker.provider = None
    outcome = worker.run(stored.principal, engagement)
    assert outcome.stop_reason == 'provider_unconfigured' and outcome.attempts == ()
    result = CompletionJournal(stored.engine).read(stored.principal, engagement)
    assert result.outcome == outcome and result.report.document().attempts == ()
    reads = len(data.calls)
    worker.provider = provider
    assert worker.run(stored.principal, engagement) == outcome
    assert len(data.calls) == reads and not provider.calls
    assert worker.completions.finish(stored.principal, engagement, stop_reason='changed_configuration') == result
    reader = replace(stored.principal, actions=frozenset({'read_attempts'}))
    assert worker.completions.read(reader, engagement) == result
    with pytest.raises(PermissionError):
        worker.completions.finish(reader, engagement, stop_reason='provider_unconfigured')
    with stored.engine.connect() as conn:
        key = worker.completions.key(stored.principal, engagement)
        assert conn.execute(text('SELECT count(*) FROM planning.reservations WHERE tenant_id=:tenant '
            'AND project_id=:project AND engagement_id=:engagement'), key).scalar_one() == 0
    with pytest.raises(DBAPIError), stored.engine.begin() as conn:
        conn.execute(text('DELETE FROM planning.checkpoint_execution_reports WHERE engagement_id=:engagement'),
                     {'engagement': engagement})


def test_success_report_survives_replacement_and_preserves_ticket(stored):
    worker, _, provider, intake = setup(stored)
    engagement = intake.planning.document().reference.engagement_id
    outcome = worker.run(stored.principal, engagement)
    result = worker.completions.read(stored.principal, engagement)
    assert result.outcome == outcome and result.report.document().stop_reason == 'abstained'
    replacement = CheckpointWorker(stored.engine, None, None, None, timeout_seconds=1)
    assert replacement.run(stored.principal, engagement) == outcome
    assert worker.dispatch.issue(stored.principal, outcome.latest.binding, 1) is None
    assert len(provider.calls) == 1
    binding = AttemptBinding(intake.planning, 2)
    packet = worker._packet(stored.principal, intake)
    with pytest.raises(ValueError, match='checkpoint_execution_completed'):
        worker.dispatch.ledger.reserve(stored.principal, binding, packet.context.budget_policy(worker.templates))
    with pytest.raises(ValueError, match='checkpoint_execution_completed'):
        worker.journal.begin_attempt(stored.principal, binding)


def test_reserved_but_unissued_attempt_stays_held_without_fake_observation(stored):
    worker, _, _, intake = setup(stored)
    engagement = intake.planning.document().reference.engagement_id
    packet = worker._packet(stored.principal, intake)
    binding = AttemptBinding(intake.planning, 1)
    policy = packet.context.budget_policy(worker.templates)
    original = worker.dispatch.ledger.reserve(stored.principal, binding, policy)
    report = worker.completions.finish(stored.principal, engagement, stop_reason='execution_processing_unavailable')
    assert report.outcome.attempts == ()
    assert worker.dispatch.ledger.reserve(stored.principal, binding, policy) == original
    with pytest.raises(ValueError, match='checkpoint_execution_completed'):
        worker.dispatch.issue(stored.principal, binding, 30)
    observed = Observation.record(binding, CapturedOutput(b'', False), 'unknown', 'fixture', unknown_usage())
    with pytest.raises(ValueError, match='checkpoint_execution_completed'):
        worker.journal.record(stored.principal, binding, observed)
    assert worker.journal.read_attempt(stored.principal, binding.reference()).observation is None


def test_inflight_call_prevents_false_zero_call_finalization(stored):
    worker, _, provider, intake = setup(stored)
    engagement = intake.planning.document().reference.engagement_id
    entered, release = Event(), Event()
    original = provider.reply
    def held(*args, **kwargs):
        entered.set()
        assert release.wait(30)
        return original(*args, **kwargs)
    provider.reply = held
    with ThreadPoolExecutor(max_workers=1) as pool:
        running = pool.submit(worker.run, stored.principal, engagement)
        try:
            assert entered.wait(30)
            with pytest.raises(ValueError, match='completion_attempt_pending'):
                worker.completions.finish(stored.principal, engagement, stop_reason='provider_unconfigured')
            assert worker.completions.read(stored.principal, engagement) is None
        finally:
            release.set()
        assert running.result(30).stop_reason == 'abstained'
    assert worker.completions.read(stored.principal, engagement).report.document().stop_reason == 'abstained'


def test_report_http_absence_then_exact_read_only_original(stored):
    worker, _, _, intake = setup(stored)
    engagement = intake.planning.document().reference.engagement_id
    with client(stored) as http:
        path = '/v2/supervision/execution/' + engagement
        headers = {'Authorization': 'Bearer ' + READ}
        assert http.get(path, headers=headers).status_code == 404
        worker.run(stored.principal, engagement)
        expected = worker.completions.read(stored.principal, engagement).report.document()
        assert http.get(path, headers=headers).json() == expected.model_dump(mode='json')
        assert http.get(path).status_code == 401
        assert http.get(path, headers={'Authorization': 'Bearer ' + FOREIGN}).status_code == 404
        assert http.get(path + '?actor=other', headers=headers).status_code == 422


def test_unsettled_capture_and_invalid_stop_cannot_create_report(stored):
    worker, _, _, intake = setup(stored)
    engagement = intake.planning.document().reference.engagement_id
    binding = AttemptBinding(intake.planning, 1)
    packet = worker._packet(stored.principal, intake)
    worker.dispatch.ledger.reserve(stored.principal, binding, packet.context.budget_policy(worker.templates))
    ticket = worker.dispatch.issue(stored.principal, binding, 30)
    observed = Observation.record(binding, CapturedOutput(b'bad', True), 'invalid', 'fixture', unknown_usage())
    worker.dispatch.complete(stored.principal, binding, ticket, observed)
    with pytest.raises(ValueError, match='completion_settlement_missing'):
        worker.completions.finish(stored.principal, engagement, stop_reason='execution_processing_unavailable')
    worker.settlements.settle(stored.principal, binding)
    with pytest.raises(ValueError, match='completion_status_mismatch'):
        worker.completions.finish(stored.principal, engagement, stop_reason='proposed')
    assert worker.completions.read(stored.principal, engagement) is None
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker.completions.finish, stored.principal, engagement,
            stop_reason='execution_processing_unavailable') for _ in range(2)]
        a, b = (item.result(30) for item in futures)
    assert a == b and len(a.outcome.attempts) == 1
    with pytest.raises(ValueError, match='stored_supervision_request_mismatch|request_actor_mismatch|actor_mismatch'):
        worker.completions.read(replace(stored.principal, actor_id='foreign'), engagement)


def test_late_diagnostic_does_not_change_completed_primary_report(stored):
    worker, _, _, intake = setup(stored)
    engagement = intake.planning.document().reference.engagement_id
    binding = AttemptBinding(intake.planning, 1)
    packet = worker._packet(stored.principal, intake)
    worker.dispatch.ledger.reserve(stored.principal, binding, packet.context.budget_policy(worker.templates))
    ticket = worker.dispatch.issue(stored.principal, binding, 1)
    time.sleep(max(0, ticket.deadline.timestamp() - time.time()) + .03)
    worker.dispatch.recover(stored.principal, binding)
    worker.settlements.settle(stored.principal, binding)
    before = worker.completions.finish(stored.principal, engagement, stop_reason='execution_processing_unavailable')
    late = Observation.record(binding, CapturedOutput(b'late', True), 'invalid', 'fixture', unknown_usage())
    worker.dispatch.complete(stored.principal, binding, ticket, late)
    assert worker.dispatch.read_late(stored.principal, binding) == late
    assert worker.completions.read(stored.principal, engagement) == before
