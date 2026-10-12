from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from amphora_contracts_campaign_curation import CurationReceiptQuery
from amphora_agent_planning.curation_jobs.journal import CurationJobs, key_for
from ..curation_intake.support import environment


def setup(stored):
    principal, raw, intake = environment(stored)
    receipt = intake.receive(principal, raw)
    worker = replace(principal, actions=frozenset({'execute_curations'}))
    return principal, worker, intake, receipt, CurationJobs(stored.engine)


def expire(stored, principal, curation_id):
    with stored.engine.begin() as conn:
        conn.execute(text('UPDATE planning.curation_leases SET lease_until=clock_timestamp()-interval \'1 second\' '
            'WHERE tenant_id=:tenant AND project_id=:project AND curation_id=:curation'), key_for(principal, curation_id))


def test_replacement_fences_old_worker_and_preserves_original_receipt(stored):
    principal, worker, intake, receipt, jobs = setup(stored)
    identity = receipt.reference.curation_id
    first = jobs.claim(worker, identity, 'worker-a')
    assert first.progress.view.receipt.phase == 'assembling'
    assert first.progress.view.receipt.revision == 1
    assert intake.read(principal, identity) == first.progress.view
    query = CurationReceiptQuery(identity=receipt.identity, request_sha256=receipt.request_sha256)
    assert intake.receipt(principal, query) == receipt
    assert jobs.claim(worker, identity, 'worker-b') is None
    expire(stored, worker, identity)
    with pytest.raises(ValueError, match='curation_lease_lost'):
        jobs.heartbeat(worker, first)
    replacement = CurationJobs(stored.engine)
    second = replacement.claim(worker, identity, 'worker-a')
    assert second.fence != first.fence and second.progress.view == first.progress.view
    for action in [lambda: jobs.heartbeat(worker, first), lambda: jobs.fail(worker, first, 'stale')]:
        with pytest.raises(ValueError, match='curation_lease_lost'): action()
    replacement.heartbeat(worker, second)
    final = replacement.fail(worker, second, 'source_unavailable')
    assert final.receipt.phase == 'failed' and final.receipt.revision == 2
    assert final.provider is None and final.proposal is None
    assert intake.read(principal, identity) == final
    assert intake.receipt(principal, query) == receipt
    assert replacement.claim(worker, identity, 'worker-c') is None


def test_concurrent_claim_has_one_winner_and_no_provider_attempt(stored):
    principal, worker, _, receipt, jobs = setup(stored)
    gate = Barrier(2)
    def claim(name):
        gate.wait(timeout=5)
        return jobs.claim(worker, receipt.reference.curation_id, name)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(claim, name) for name in ('one', 'two')]
        results = [future.result(timeout=15) for future in futures]
    assert sum(result is not None for result in results) == 1
    with stored.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM planning.attempts WHERE tenant_id=:tenant AND project_id=:project'),
            key_for(principal, receipt.reference.curation_id)).scalar_one() == 0


def test_grants_scope_and_actor_do_not_leak_or_execute(stored):
    principal, worker, _, receipt, jobs = setup(stored)
    identity = receipt.reference.curation_id
    with pytest.raises(PermissionError): jobs.claim(principal, identity, 'browser')
    assert jobs.claim(replace(worker, actor_id='other'), identity, 'foreign') is None
    foreign = replace(worker, scope=worker.scope.model_copy(update={'project_id': 'other'}))
    assert jobs.claim(foreign, identity, 'foreign') is None
    lease = jobs.claim(worker, identity, 'original')
    with pytest.raises(ValueError, match='curation_lease_unavailable'):
        jobs.fail(foreign, lease, 'foreign')
    with pytest.raises(PermissionError): jobs.heartbeat(principal, lease)
    with pytest.raises(PermissionError): jobs.fail(principal, lease, 'browser')


def test_claim_and_progress_rollback_are_atomic(stored, monkeypatch):
    principal, worker, intake, receipt, jobs = setup(stored)
    identity = receipt.reference.curation_id
    append = jobs._append
    def fail(*args):
        append(*args)
        raise RuntimeError('after_insert')
    monkeypatch.setattr(jobs, '_append', fail)
    with pytest.raises(RuntimeError): jobs.claim(worker, identity, 'one')
    assert intake.read(principal, identity).receipt == receipt
    monkeypatch.setattr(jobs, '_append', append)
    lease = jobs.claim(worker, identity, 'two')
    monkeypatch.setattr(jobs, '_append', fail)
    with pytest.raises(RuntimeError): jobs.fail(worker, lease, 'unavailable')
    assert intake.read(principal, identity) == lease.progress.view
    monkeypatch.setattr(jobs, '_append', append)
    assert jobs.fail(worker, lease, 'unavailable').receipt.revision == 2


@pytest.mark.parametrize('seconds', [0, 61, True, 1.5])
def test_lease_bound(stored, seconds):
    _, worker, _, receipt, jobs = setup(stored)
    with pytest.raises(ValueError, match='curation_lease_bound'):
        jobs.claim(worker, receipt.reference.curation_id, 'worker', lease_seconds=seconds)


def test_history_is_insert_only_and_bad_failure_does_not_change_it(stored):
    principal, worker, intake, receipt, jobs = setup(stored)
    lease = jobs.claim(worker, receipt.reference.curation_id, 'worker')
    with pytest.raises(ValueError): jobs.fail(worker, lease, '')
    assert intake.read(principal, lease.curation_id) == lease.progress.view
    for sql in ['UPDATE planning.curation_progress SET revision=revision WHERE false',
                'DELETE FROM planning.curation_progress WHERE false',
                'DELETE FROM planning.curation_leases WHERE false']:
        with pytest.raises(DBAPIError), stored.engine.begin() as conn: conn.execute(text(sql))
