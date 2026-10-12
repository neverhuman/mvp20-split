from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from threading import Barrier

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from amphora_agent_planning.capability_fulfillment.journal import FulfillmentJournal
from amphora_agent_planning.capability_fulfillment.original import OriginalFulfillment
from amphora_agent_planning.curation_intake.commands import FulfillmentCommand
from ..capability_requests.test_reads import recorded
from ..curation_intake.test_commands import fulfillment

pytestmark = pytest.mark.postgres


def setup(stored):
    principal, lease, intake, _, _, _ = recorded(stored)
    reference = intake.read(principal, lease.curation_id).capability_requests[0]
    raw = fulfillment()
    raw['identity'].update(actor_id=principal.actor_id, scope=principal.scope.model_dump())
    raw['payload']['request'] = reference.model_dump(mode='json')
    raw['payload']['acceptance_evidence'][0]['scope'] = principal.scope.model_dump()
    owner = replace(principal, actions=frozenset({'fulfill_capabilities'}))
    return owner, raw, FulfillmentJournal(stored.engine)


def row(stored, owner):
    with stored.engine.connect() as conn:
        return conn.execute(text('SELECT * FROM planning.capability_fulfillments WHERE project_id=:project'),
            {'project': owner.scope.project_id}).mappings().one()


def test_original_receipt_and_frozen_gap_survive_replacement(stored):
    owner, raw, journal = setup(stored)
    first = journal.receive(owner, json.dumps(raw))
    assert first.status == 'pending' and first.reason_code is None
    original = OriginalFulfillment.restore(row(stored, owner))
    assert original.receipt == first and original.capability.reference == first.specification.request
    assert FulfillmentJournal(stored.engine).receive(owner, json.dumps(raw)) == first
    changed = json.loads(json.dumps(raw))
    changed['payload']['release']['descriptor_sha256'] = 'e' * 64
    assert FulfillmentCommand.restore(json.dumps(changed)).fulfillment_id == original.incoming.fulfillment_id
    with pytest.raises(ValueError, match='fulfillment_command_conflict'):
        journal.receive(owner, json.dumps(changed))
    worker = replace(owner, actions=frozenset({'execute_curations'}))
    original.require_worker(worker)
    with pytest.raises(PermissionError): journal.receive(worker, json.dumps(raw))
    with pytest.raises(PermissionError): original.require_worker(owner)


def test_scope_actor_grants_and_missing_original_cannot_admit(stored):
    owner, raw, journal = setup(stored)
    for denied in (replace(owner, actor_id='other'), replace(owner, actions=frozenset({'read_capabilities'})),
                   replace(owner, scope=owner.scope.model_copy(update={'project_id': 'other'}))):
        with pytest.raises(PermissionError): journal.receive(denied, json.dumps(raw))
    other = replace(owner, actor_id='other')
    raw['identity']['actor_id'] = 'other'
    with pytest.raises(ValueError, match='capability_request_not_found'): journal.receive(other, json.dumps(raw))
    raw['identity']['actor_id'] = owner.actor_id
    raw['payload']['request']['request_id'] = 'missing'
    with pytest.raises(ValueError, match='capability_request_not_found'): journal.receive(owner, json.dumps(raw))


def test_concurrent_retry_and_transaction_rollback(stored, monkeypatch):
    owner, raw, journal = setup(stored)
    insert = journal._insert
    def interrupted(conn, key, original):
        insert(conn, key, original)
        raise RuntimeError('before_commit')
    monkeypatch.setattr(journal, '_insert', interrupted)
    with pytest.raises(RuntimeError, match='before_commit'): journal.receive(owner, json.dumps(raw))
    with stored.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM planning.capability_fulfillments WHERE project_id=:project'),
            {'project': owner.scope.project_id}).scalar_one() == 0
    monkeypatch.setattr(journal, '_insert', insert)
    gate = Barrier(2)
    def submit():
        gate.wait(timeout=5)
        return journal.receive(owner, json.dumps(raw))
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(submit) for _ in range(2)]
        receipts = [job.result(timeout=15) for job in jobs]
    assert receipts[0] == receipts[1]
    assert OriginalFulfillment.restore(row(stored, owner)).receipt == receipts[0]


def test_service_cannot_rewrite_evidence_and_restore_detects_corruption(stored):
    owner, raw, journal = setup(stored)
    journal.receive(owner, json.dumps(raw))
    original = dict(row(stored, owner))
    for field, value in [('command_sha256', '0' * 64), ('receipt_sha256', '0' * 64),
                         ('capability_sha256', '0' * 64), ('request_id', 'unrelated')]:
        with pytest.raises(ValueError, match='stored_fulfillment_'):
            OriginalFulfillment.restore({**original, field: value})
    for operation in ('UPDATE planning.capability_fulfillments SET request_id=request_id',
                      'DELETE FROM planning.capability_fulfillments'):
        with stored.engine.begin() as conn:
            with pytest.raises(DBAPIError):
                conn.execute(text(operation + ' WHERE project_id=:project'), {'project': owner.scope.project_id})
