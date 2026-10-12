import json
from uuid import uuid4
from dataclasses import replace

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.curation_intake.commands import CurationCommand
from amphora_agent_planning.curation_intake.journal import CurationJournal
from amphora_agent_planning.curation_jobs.journal import CurationJobs
from amphora_agent_planning.curation_runtime import CurationRuntimeContext
from amphora_agent_planning.curation_declaration.origin import DeclarationOrigin
from amphora_agent_planning.curation_declaration.journal import DeclarationJournal
from amphora_agent_planning.curation_declaration.workflow import DeclarationPublisher
from amphora_tool_protocol import ArtifactClient, WorkerIdentity, TransportLost
from ..curation_policy.test_policy import declared
from ..curation_runtime.test_context import case
from ..curation_jobs.test_journal import expire
from ..publication.test_workflow import DataPeer


def setup(stored):
    policy, incoming, _, _ = declared()
    raw = json.loads(incoming.command.canonical_bytes)
    raw['identity']['command_id'] = uuid4().hex
    incoming = CurationCommand.restore(json.dumps(raw))
    seed = policy.seed(incoming)
    _, _, draft, run = case()
    original = CurationRuntimeContext.bind(seed, draft, run)
    principal = Principal(incoming.command.identity.actor_id, incoming.command.identity.scope,
        frozenset({'record_curations', 'read_curations', 'execute_curations'}))
    CurationJournal(stored.engine, {'synthetic'}).receive(principal, incoming.command.canonical_bytes)
    lease = CurationJobs(stored.engine).claim(principal, incoming.curation_id, 'worker', lease_seconds=60)
    journal = DeclarationJournal(stored.engine)
    origin = DeclarationOrigin.bind(policy, original)
    peer = DataPeer(origin, origin.artifact())
    client = ArtifactClient(peer, WorkerIdentity(principal.actor_id, principal.scope))
    return principal, lease, journal, DeclarationPublisher(journal, client), peer, policy, original


def test_origin_rebuilds_exact_body_and_records_reviewed_roots():
    policy, _, original, reviewed = declared()
    origin = DeclarationOrigin.bind(policy, original)
    assert DeclarationOrigin.restore(origin.canonical) == origin
    artifact = origin.artifact()
    assert artifact.body == reviewed.declaration.canonical
    assert artifact.content.media_type == 'text/plain'
    assert artifact.declaration.transformation.sha256 == origin.sha256
    assert len(artifact.declaration.inputs) == 4
    value = json.loads(origin.canonical)
    value['command']['payload']['direction'] = 'changed'
    with pytest.raises(ValueError): DeclarationOrigin.restore(json.dumps(value).encode())


@pytest.mark.postgres
@pytest.mark.parametrize('loss', ['none', 'begin', 'put', 'finalize'])
def test_publication_recovery_preserves_original_inputs_and_upload_commands(stored, loss):
    principal, lease, journal, publisher, peer, policy, original = setup(stored)
    peer.lost_begin = loss == 'begin'
    peer.lost_put = loss == 'put'
    peer.lost_finalize = loss == 'finalize'
    if loss in {'put', 'finalize'}:
        with pytest.raises((TransportLost, ValueError)):
            publisher.publish(principal, lease, policy=policy, original=original)
        peer.lost_put = peer.lost_finalize = peer.final_lookup_down = False
        expire(stored, principal, lease.curation_id)
        lease = CurationJobs(stored.engine).claim(principal, lease.curation_id, 'replacement', lease_seconds=60)
    result = publisher.publish(principal, lease, policy=policy, original=original)
    assert result.attempt.stage == 'finalized'
    assert len(peer.uploads) == (2 if loss == 'put' else 1)
    calls = list(peer.calls)
    assert publisher.publish(principal, lease) == result
    assert peer.calls == calls
    assert DeclarationJournal(stored.engine).read(principal, lease.curation_id) == result
    assert result.identity.reviewed() == policy.declare(original)
    assert len([path for method, path, _ in calls if method == 'PUT']) == len(peer.uploads)


@pytest.mark.postgres
def test_expired_worker_and_browser_cannot_create_declaration(stored):
    principal, lease, journal, _, _, policy, original = setup(stored)
    browser = replace(principal, actions=frozenset({'read_curations'}))
    with pytest.raises(PermissionError): journal.register(browser, lease, policy, original)
    expire(stored, principal, lease.curation_id)
    with pytest.raises(ValueError, match='curation_lease_lost'):
        journal.register(principal, lease, policy, original)
    assert journal.read(principal, lease.curation_id) is None


@pytest.mark.postgres
def test_initial_event_failure_rolls_back_origin(stored, monkeypatch):
    principal, lease, journal, _, _, policy, original = setup(stored)
    insert = journal._event
    def fail(*args):
        insert(*args)
        raise RuntimeError('rollback')
    monkeypatch.setattr(journal, '_event', fail)
    with pytest.raises(RuntimeError): journal.register(principal, lease, policy, original)
    assert journal.read(principal, lease.curation_id) is None


@pytest.mark.postgres
def test_foreign_client_rejects_before_any_publication_record(stored):
    principal, lease, journal, _, peer, policy, original = setup(stored)
    client = ArtifactClient(peer, WorkerIdentity('other', principal.scope))
    with pytest.raises(ValueError, match='curation_declaration_client'):
        DeclarationPublisher(journal, client).publish(principal, lease, policy=policy, original=original)
    assert journal.read(principal, lease.curation_id) is None and peer.calls == []


@pytest.mark.postgres
def test_event_cas_and_old_fence_cannot_advance_replacement(stored):
    from ..publication.test_values import receipts
    principal, lease, journal, _, _, policy, original = setup(stored)
    initial = journal.register(principal, lease, policy, original)
    upload, *_ = receipts(initial.identity, initial.payload.artifact, initial.attempt)
    data = upload.model_dump(mode='json')
    result = journal.advance(principal, lease, initial.position, 'begun', data)
    with pytest.raises(ValueError, match='curation_declaration_position'):
        journal.advance(principal, lease, initial.position, 'begun', data)
    expire(stored, principal, lease.curation_id)
    replacement = CurationJobs(stored.engine).claim(principal, lease.curation_id, 'new-worker', lease_seconds=60)
    with pytest.raises(ValueError, match='curation_lease_lost'):
        journal.advance(principal, lease, result.position, 'streaming')
    assert journal.advance(principal, replacement, result.position, 'streaming').attempt.stage == 'streaming'
