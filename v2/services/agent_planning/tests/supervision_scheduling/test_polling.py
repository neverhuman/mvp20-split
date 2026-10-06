"""Actual Planning discovery with independently journaled worker/publication boundaries."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_agent_planning.supervision_client import ExchangeUnavailable
from amphora_agent_planning.supervision_publication.exchange import (
    CaptureResponseJournal,
)
from amphora_agent_planning.supervision_publication.workflow import CaptureResponder
from amphora_agent_planning.supervision_scheduling import (
    PlanningCheckpointPoller,
    PlanningStep,
)
from amphora_agent_planning.supervision_scheduling.discovery import WorkDiscovery

from ..supervision_execution.test_worker import setup
from ..supervision_publication.runtime_peer import RuntimePeer
from ..supervision_publication.test_journal import expired_with_late
from ..supervision_publication.test_workflow import publisher

pytestmark = pytest.mark.postgres


def test_execution_discovered_and_completion_excluded_after_restart(stored):
    worker, _, provider, intake = setup(stored)
    worker.provider = None
    poller = PlanningCheckpointPoller(stored.engine, worker, None, None)
    result = poller.tick(stored.principal)
    assert result.stage == 'execution' and result.reason == 'provider_unconfigured'
    assert result.engagement_id == intake.planning.document().reference.engagement_id
    assert PlanningCheckpointPoller(stored.engine, worker, None, None).tick(stored.principal) is None
    assert provider.calls == []


def test_execution_then_capture_delivery_and_restart_are_once_only(stored):
    worker, _, provider, intake = setup(stored)
    poller = PlanningCheckpointPoller(stored.engine, worker, None, None)
    assert poller.tick(stored.principal).reason == 'abstained'
    completion = worker.completions.read(stored.principal, intake.planning.document().reference.engagement_id)
    attempt = completion.report.document().attempts[-1].attempt
    pub, _ = publisher(stored, attempt)
    with RuntimePeer(stored.principal) as runtime:
        responder = CaptureResponder(CaptureResponseJournal(pub.journal), runtime.client)
        poller = PlanningCheckpointPoller(stored.engine, worker, pub, responder)
        assert poller.tick(stored.principal).stage == 'capture_response'
        assert poller.tick(stored.principal) is None
        assert PlanningCheckpointPoller(stored.engine, worker, pub, responder).tick(stored.principal) is None
        assert len(provider.calls) == 1


def test_scope_actor_and_required_grants_bound_discovery(stored):
    worker, _, _, _ = setup(stored)
    poller = PlanningCheckpointPoller(stored.engine, worker, None, None)
    assert poller.tick(replace(stored.principal, actor_id='foreign')) is None
    assert poller.tick(replace(stored.principal,
        scope=stored.principal.scope.model_copy(update={'project_id': 'foreign'}))) is None
    with pytest.raises(PermissionError):
        poller.tick(replace(stored.principal, actions=frozenset({'read_attempts'})))


def test_primary_and_late_discovery_remain_distinct_and_fair(stored):
    attempt = expired_with_late(stored)
    discovery = WorkDiscovery(stored.engine)
    rows = [discovery.next(stored.principal, 'capture') for _ in range(4)]
    assert [row.kind for row in rows] == ['late', 'primary', 'late', 'primary']
    assert all(row.engagement_id == attempt.engagement.engagement_id and row.ordinal == attempt.ordinal for row in rows)


def test_rejected_upload_excluded_without_sending_false_success(stored):
    worker, _, _, intake = setup(stored)
    result = worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    pub, peer = publisher(stored, result.latest.binding.reference())
    peer.reject = True
    poller = PlanningCheckpointPoller(stored.engine, worker, pub, None)
    assert poller.tick(stored.principal).stage == 'capture_rejected'
    assert poller.tick(stored.principal) is None


@pytest.mark.parametrize('error,reason', [(ExchangeUnavailable('fixture'), 'peer_uncertain'),
    (ValueError('capture_lease_unavailable'), 'capture_lease_unavailable')])
def test_capture_uncertainty_preserves_discoverable_owned_work(stored, error, reason):
    worker, _, _, intake = setup(stored)
    worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    def fail(*args, **kwargs):
        raise error
    poller = PlanningCheckpointPoller(stored.engine, worker, SimpleNamespace(publish=fail), None)
    assert poller.tick(stored.principal).reason == reason
    assert poller.discovery.next(stored.principal, 'capture') is not None


def test_alternates_lanes_even_when_capture_is_pending():
    principal = SimpleNamespace(scope=SimpleNamespace(tenant_id='t', project_id='p'), actor_id='a', require=lambda *_: None)
    poller = PlanningCheckpointPoller(None, SimpleNamespace(run=lambda *_: SimpleNamespace(stop_reason='attempt_pending')),
                                     None, None)
    seen = []
    def next_item(actor, lane):
        seen.append(lane)
        return SimpleNamespace(engagement_id='e')
    poller.discovery = SimpleNamespace(next=next_item)
    poller._capture = lambda *_: PlanningStep('capture_pending', 'e')
    assert [poller.tick(principal).stage for _ in range(4)] == ['execution', 'capture_pending'] * 2
    assert seen == ['execution', 'capture'] * 2


@pytest.mark.parametrize('mode', ['rejected', 'readback_down'])
def test_response_terminal_filter_requires_exact_readback_or_rejection(stored, mode):
    worker, _, _, intake = setup(stored)
    result = worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    pub, _ = publisher(stored, result.latest.binding.reference())
    with RuntimePeer(stored.principal) as runtime:
        if mode == 'rejected':
            runtime.outcome = 'rejected'
        else:
            runtime.readback_down = True
        poller = PlanningCheckpointPoller(stored.engine, worker, pub,
            CaptureResponder(CaptureResponseJournal(pub.journal), runtime.client))
        result = poller.tick(stored.principal)
        if mode == 'readback_down':
            assert result.stage == 'capture_pending'
            assert poller.discovery.next(stored.principal, 'capture') is not None
            runtime.readback_down = False
            assert poller.tick(stored.principal).reason == 'recorded'
        else:
            assert result.reason == 'rejected'
        assert poller.tick(stored.principal) is None
        assert sum(path == '/v1/supervision/responses' for _, path, _ in runtime.calls) == 1


def test_unexpected_capture_error_is_not_uncertain_transport(stored):
    worker, _, _, intake = setup(stored)
    worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    def fail(*args, **kwargs):
        raise ValueError('stored_capture_identity')
    poller = PlanningCheckpointPoller(stored.engine, worker, SimpleNamespace(publish=fail), None)
    with pytest.raises(ValueError, match='stored_capture_identity'):
        poller.tick(stored.principal)


def test_sweep_bounds_and_stage_counts(monkeypatch):
    import amphora_agent_planning.supervision_scheduling.polling as module
    poller = PlanningCheckpointPoller(None, None, None, None)
    for seconds in (0, True, float('nan')):
        with pytest.raises(ValueError, match='checkpoint_polling_window'):
            poller.sweep(None, seconds=seconds)
    clock = iter([0, 0, .1, .2, 1, 1])
    monkeypatch.setattr(module.time, 'monotonic', lambda: next(clock))
    monkeypatch.setattr(module.time, 'sleep', lambda _: None)
    results = iter([None, PlanningStep('execution', 'e')])
    monkeypatch.setattr(poller, 'tick', lambda _: next(results))
    assert poller.sweep(None, seconds=1) == {'idle': 1, 'execution': 1}
