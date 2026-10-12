import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_contracts_campaign_curation import CurationReceiptQuery
from amphora_agent_planning.curation_intake.journal import CurationJournal
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from .support import environment


def test_original_receipt_survives_replacement_policy_retirement_and_read_only_recovery(stored):
    principal, raw, journal = environment(stored)
    first = journal.receive(principal, raw)
    replacement = CurationJournal(stored.engine, ())
    readonly = replace(principal, actions=frozenset({'read_curations'}))
    assert replacement.receive(principal, raw) == first
    query = CurationReceiptQuery(identity=first.identity, request_sha256=first.request_sha256)
    assert replacement.receipt(readonly, query) == first
    view = replacement.read(readonly, first.reference.curation_id)
    assert view.receipt == first and view.provider is None and view.proposal is None
    assert view.validated_draft is None
    with pytest.raises(PermissionError): replacement.receive(readonly, raw)
    changed = json.loads(raw)
    changed['payload']['direction'] = 'Changed after recording'
    with pytest.raises(ValueError, match='curation_command_conflict'):
        replacement.receive(principal, json.dumps(changed))
    with pytest.raises(ValueError, match='curation_receipt_conflict'):
        replacement.receipt(readonly, query.model_copy(update={'request_sha256': '0' * 64}))
    changed['identity']['command_id'] = 'new'
    with pytest.raises(ValueError, match='curation_policy_unavailable'):
        replacement.receive(principal, json.dumps(changed))
    with stored.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM planning.attempts WHERE tenant_id=:tenant AND project_id=:project'),
            {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id}).scalar_one() == 0


def test_concurrent_duplicate_clicks_create_one_original(stored):
    principal, raw, journal = environment(stored)
    gate = Barrier(2)
    def submit():
        gate.wait(timeout=5)
        return journal.receive(principal, raw)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit) for _ in range(2)]
        results = [future.result(timeout=15) for future in futures]
    assert results[0] == results[1]
    with stored.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM planning.curation_requests WHERE tenant_id=:tenant AND project_id=:project'),
            {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id}).scalar_one() == 1


def test_failure_before_commit_leaves_no_acknowledged_intent(stored, monkeypatch):
    principal, raw, journal = environment(stored)
    original = journal._insert
    ids = []
    def fail(conn, key, record):
        original(conn, key, record)
        ids.append(record.incoming.curation_id)
        raise RuntimeError('after_insert_before_commit')
    monkeypatch.setattr(journal, '_insert', fail)
    with pytest.raises(RuntimeError): journal.receive(principal, raw)
    assert journal.read(principal, ids[0]) is None
    monkeypatch.setattr(journal, '_insert', original)
    assert journal.receive(principal, raw).reference.curation_id == ids[0]


def test_scoped_visibility_and_insert_only_history(stored):
    principal, raw, journal = environment(stored)
    first = journal.receive(principal, raw)
    assert journal.read(replace(principal, actor_id='other'), first.reference.curation_id) is None
    foreign = replace(principal, scope=principal.scope.model_copy(update={'project_id': 'other'}))
    assert journal.read(foreign, first.reference.curation_id) is None
    assert journal.read(principal, 'missing') is None
    for sql in ['DELETE FROM planning.curation_requests WHERE false',
                'UPDATE planning.curation_requests SET command_id=command_id WHERE false']:
        with pytest.raises(DBAPIError), stored.engine.begin() as conn:
            conn.execute(text(sql))


def test_receipt_bytes_do_not_depend_on_reader_session_timezone(stored):
    principal, raw, journal = environment(stored)
    receipt = journal.receive(principal, raw)
    engine = create_engine(stored.engine.url, connect_args={'options': '-c timezone=America/Chicago'})
    try:
        other = CurationJournal(engine, ())
        query = CurationReceiptQuery(identity=receipt.identity, request_sha256=receipt.request_sha256)
        assert other.receipt(principal, query).model_dump_json() == receipt.model_dump_json()
    finally:
        engine.dispose()
