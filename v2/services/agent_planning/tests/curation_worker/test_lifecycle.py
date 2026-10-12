import json
import time
from uuid import uuid4
from dataclasses import replace

import pytest
from amphora_agent_planning.curation_jobs.journal import CurationJobs
from amphora_agent_planning.curation_worker.discovery import CurationDiscovery
from amphora_agent_planning.curation_worker.lease import LeaseKeeper
from ..curation_jobs.test_journal import setup, expire
from ..curation_preparation.test_link import setup as preparation_setup

pytestmark = pytest.mark.postgres


def test_discovery_scope_policy_rotation_and_active_or_terminal_exclusion(stored):
    principal, worker, intake, receipt, jobs = setup(stored)
    # Use the original command bytes through the owned test fixture, not a view as a write.
    from ..curation_intake.support import environment
    _, raw, _ = environment(stored)
    value = json.loads(raw)
    value['identity']['command_id'] = uuid4().hex
    second = intake.receive(principal, json.dumps(value).encode())
    ids = sorted([receipt.reference.curation_id, second.reference.curation_id])
    discovery = CurationDiscovery(stored.engine, ['synthetic'])
    assert [discovery.next(worker) for _ in range(3)] == [*ids, ids[0]]
    assert CurationDiscovery(stored.engine, ['unconfigured']).next(worker) is None
    assert discovery.next(replace(worker, actor_id='foreign')) is None
    with pytest.raises(PermissionError): discovery.next(principal)
    lease = jobs.claim(worker, ids[0], 'worker')
    assert discovery.next(worker) == ids[1]
    jobs.fail(worker, lease, 'test_failure')
    assert CurationDiscovery(stored.engine, ['synthetic']).next(worker) == ids[1]
    other = jobs.claim(worker, ids[1], 'worker')
    assert discovery.next(worker) is None
    jobs.release(worker, other)
    assert discovery.next(worker) == ids[1]


def test_periodic_renewal_and_graceful_release_preserve_original_progress(stored):
    _, worker, _, receipt, jobs = setup(stored)
    lease = jobs.claim(worker, receipt.reference.curation_id, 'worker', lease_seconds=1)
    with LeaseKeeper(jobs, worker, lease, interval_seconds=0.1, lease_seconds=1) as keeper:
        time.sleep(1.3)
        assert jobs.claim(worker, lease.curation_id, 'replacement') is None
        assert keeper.current().progress == lease.progress
    replacement = jobs.claim(worker, lease.curation_id, 'replacement')
    assert replacement is not None and replacement.fence != lease.fence
    assert not jobs.release(worker, lease)
    jobs.heartbeat(worker, replacement)


def test_refresh_survives_real_preparation_progress_transition(stored):
    principal, _, _, prepared, lease, preparation = preparation_setup(stored)
    jobs = CurationJobs(stored.engine)
    with LeaseKeeper(jobs, principal, lease, interval_seconds=0.05) as keeper:
        linked = preparation.freeze(principal, lease, prepared)
        updated = keeper.current()
        assert updated.progress == linked.progress and updated.fence == lease.fence
        assert updated.progress.view.receipt.phase == 'awaiting_provider'


def test_replaced_worker_stops_heartbeat_and_cannot_release_successor(stored):
    _, worker, _, receipt, jobs = setup(stored)
    lease = jobs.claim(worker, receipt.reference.curation_id, 'worker')
    with LeaseKeeper(jobs, worker, lease, interval_seconds=0.05) as keeper:
        expire(stored, worker, lease.curation_id)
        replacement = jobs.claim(worker, lease.curation_id, 'replacement')
        assert keeper.stop.wait(2)
        with pytest.raises(ValueError, match='curation_lease_lost'): keeper.current()
    jobs.heartbeat(worker, replacement)


def test_background_failure_is_redacted_and_releases_only_original_fence(stored, monkeypatch):
    _, worker, _, receipt, jobs = setup(stored)
    lease = jobs.claim(worker, receipt.reference.curation_id, 'worker')
    with LeaseKeeper(jobs, worker, lease, interval_seconds=0.05) as keeper:
        def fail(*args, **kwargs): raise RuntimeError('database credential must not escape')
        monkeypatch.setattr(jobs, 'refresh', fail)
        assert keeper.stop.wait(2)
        with pytest.raises(ValueError, match='^curation_heartbeat_unavailable$'): keeper.current()
    assert CurationJobs(stored.engine).claim(worker, lease.curation_id, 'replacement') is not None


def test_terminal_progress_is_read_without_renewal(stored):
    _, worker, _, receipt, jobs = setup(stored)
    lease = jobs.claim(worker, receipt.reference.curation_id, 'worker')
    with LeaseKeeper(jobs, worker, lease, interval_seconds=0.05) as keeper:
        final = jobs.fail(worker, lease, 'test_failure')
        assert keeper.stop.wait(2)
        assert keeper.current().progress.view == final
    assert jobs.claim(worker, lease.curation_id, 'replacement') is None
