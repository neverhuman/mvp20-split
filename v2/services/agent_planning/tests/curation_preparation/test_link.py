import json
from dataclasses import replace
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from amphora_agent_planning.access import Principal
from amphora_agent_planning.curation_context import CurationIntent
from amphora_agent_planning.curation_intake.commands import CurationCommand
from amphora_agent_planning.curation_intake.journal import CurationJournal
from amphora_agent_planning.curation_jobs.journal import CurationJobs
from amphora_agent_planning.curation_preparation.link import CurationPreparationJournal
from ..curation_jobs.test_journal import expire
from .test_assembly import assembly


def setup(stored):
    assembler, original, *_ = assembly()
    raw = json.loads(original.canonical)['command']
    raw['identity']['command_id'] = uuid4().hex
    incoming = CurationCommand.restore(json.dumps(raw))
    intent = CurationIntent.from_template(original.request, incoming, 'synthetic')
    principal = Principal(intent.request.document().actor_id, intent.request.document().reference.scope,
        frozenset({'record_curations', 'read_curations', 'execute_curations', 'record_requests', 'record_attempts', 'read_attempts'}))
    intake = CurationJournal(stored.engine, {'synthetic'})
    receipt = intake.receive(principal, incoming.command.canonical_bytes)
    prepared = assembler.read(intent)
    lease = CurationJobs(stored.engine).claim(principal, receipt.reference.curation_id, 'worker', lease_seconds=60)
    return principal, intake, receipt, prepared, lease, CurationPreparationJournal(stored.engine)


def test_exact_preparation_link_survives_replacement_without_provider_attempt(stored):
    principal, intake, receipt, prepared, lease, journal = setup(stored)
    empty = journal.recover(principal, lease.curation_id)
    assert empty.request is None and empty.frozen is None and empty.link is None
    original = journal.freeze(principal, lease, prepared)
    recovered = CurationPreparationJournal(stored.engine).recover(principal, lease.curation_id)
    assert recovered.link == original and recovered.frozen == original.frozen
    assert journal.freeze(principal, lease, prepared) == original
    current = intake.read(principal, lease.curation_id)
    assert current.receipt.phase == 'awaiting_provider' and current.receipt.revision == 2
    assert current.provider is None and current.proposal is None
    assert original.frozen.envelope.body == recovered.frozen.envelope.body
    request = original.frozen.preparation.packet.request
    with stored.engine.connect() as conn:
        for table in ('attempts', 'reservations', 'dispatches'):
            assert conn.execute(text('SELECT count(*) FROM planning.' + table +
                ' WHERE tenant_id=:tenant AND project_id=:project AND engagement_id=:engagement'),
                {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id,
                 'engagement': request.document().reference.engagement_id}).scalar_one() == 0


def test_crash_after_retention_before_link_recovers_exact_original_bytes(stored, monkeypatch):
    principal, intake, _, prepared, lease, journal = setup(stored)
    insert = journal._insert
    def fail(*args):
        insert(*args)
        raise RuntimeError('lost_before_commit')
    monkeypatch.setattr(journal, '_insert', fail)
    with pytest.raises(RuntimeError): journal.freeze(principal, lease, prepared)
    assert intake.read(principal, lease.curation_id).receipt.phase == 'assembling'
    recovered = CurationPreparationJournal(stored.engine).recover(principal, lease.curation_id)
    assert recovered.frozen is not None and recovered.link is None
    expire(stored, principal, lease.curation_id)
    replacement = CurationJobs(stored.engine).claim(principal, lease.curation_id, 'replacement', lease_seconds=60)
    retry = CurationPreparationJournal(stored.engine).attach(principal, replacement, recovered.frozen)
    assert retry.frozen == recovered.frozen and retry.progress.view.receipt.revision == 2
    assert intake.read(principal, lease.curation_id).receipt == retry.progress.view.receipt


def test_expired_fence_cannot_create_request_preparation_or_link(stored):
    principal, intake, _, prepared, lease, journal = setup(stored)
    expire(stored, principal, lease.curation_id)
    with pytest.raises(ValueError, match='curation_lease_lost'):
        journal.freeze(principal, lease, prepared)
    state = journal.recover(principal, lease.curation_id)
    assert state.request is None and state.frozen is None and state.link is None
    assert intake.read(principal, lease.curation_id).receipt.revision == 1


def test_competing_identical_freezes_commit_one_progress_revision(stored):
    principal, intake, _, prepared, lease, journal = setup(stored)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(journal.freeze, principal, lease, prepared) for _ in range(2)]
        outcomes = [future.result(timeout=45) for future in futures]
    assert outcomes[0] == outcomes[1]
    assert intake.read(principal, lease.curation_id).receipt.revision == 2


def test_separate_grants_and_immutable_link_history(stored):
    principal, _, _, prepared, lease, journal = setup(stored)
    browser = replace(principal, actions=frozenset({'record_curations', 'read_curations'}))
    with pytest.raises(PermissionError): journal.freeze(browser, lease, prepared)
    with pytest.raises(PermissionError): journal.recover(browser, lease.curation_id)
    assert journal.recover(replace(principal, actor_id='other'), lease.curation_id) is None
    assert journal.recover(principal, 'missing') is None
    journal.freeze(principal, lease, prepared)
    for sql in ['DELETE FROM planning.curation_preparation_links WHERE false',
                'UPDATE planning.curation_preparation_links SET manifest_sha256=manifest_sha256 WHERE false']:
        with pytest.raises(DBAPIError), stored.engine.begin() as conn: conn.execute(text(sql))


def test_lease_expiring_between_request_and_preparation_cannot_create_input(stored, monkeypatch):
    principal, _, _, prepared, lease, journal = setup(stored)
    register = journal.requests.register
    def expired_after_request(*args, **kwargs):
        result = register(*args, **kwargs)
        expire(stored, principal, lease.curation_id)
        return result
    monkeypatch.setattr(journal.requests, 'register', expired_after_request)
    with pytest.raises(ValueError, match='curation_lease_lost'):
        journal.freeze(principal, lease, prepared)
    recovered = journal.recover(principal, lease.curation_id)
    assert recovered.request is not None and recovered.frozen is None and recovered.link is None
