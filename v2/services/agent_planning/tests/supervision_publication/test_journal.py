"""Actual owner SQL, immutable upload and response history; peer receipts scripted."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_agent_planning.supervision_client.observations import RecordingObservation
from amphora_agent_planning.supervision_publication.exchange import (
    CaptureResponseJournal,
)
from amphora_agent_planning.supervision_publication.journal import CaptureJournal
from amphora_contracts_artifacts import (
    DerivationReceipt,
    DerivedUploadReceipt,
    FinalizedReceipt,
    UploadContentReceipt,
    UploadReceipt,
)
from amphora_contracts_core import ArtifactRef
from amphora_contracts_supervision import SupervisionResponse
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..supervision_client.support import receipt
from ..supervision_execution.test_worker import setup

pytestmark = pytest.mark.postgres


@pytest.fixture
def capture(stored):
    worker, _, _, intake = setup(stored)
    result = worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    return result.latest.binding.reference()


def finalized(journal, actor, state, lease):
    artifact = state.payload.artifact
    upload = DerivedUploadReceipt(upload=UploadReceipt(upload_id='capture-upload', scope=actor.scope,
        content=artifact.content), declaration=artifact.declaration)
    stream = UploadContentReceipt(upload_id='capture-upload', attempt_id='stream', generation=1)
    ref = ArtifactRef(artifact_id='capture-result', scope=actor.scope, **artifact.content.model_dump(mode='python'))
    final = FinalizedReceipt(upload_id=upload.upload.upload_id, artifact=ref)
    begin = state.attempt.begin_command(state.identity, artifact)
    derivation = DerivationReceipt(origin=begin.identity, request_sha256=begin.sha256,
        upload_id=upload.upload.upload_id, artifact=ref, declaration=artifact.declaration)
    for action, data in [('begun', upload.model_dump(mode='json')), ('streaming', None),
        ('streamed', stream.model_dump(mode='json')), ('finalizing', None),
        ('finalized', {'receipt': final.model_dump(mode='json'), 'derivation': derivation.model_dump(mode='json')})]:
        state = journal.advance(actor, lease, state.position, action, data)
    return state


def test_finalized_capture_and_exact_response_readback_survive_replacement(stored, capture):
    actor = stored.principal
    journal = CaptureJournal(stored.engine, 'data-owner')
    state = journal.register(actor, capture)
    assert state.position == 1 and journal.register(actor, capture) == state
    responses = CaptureResponseJournal(journal)
    lease = journal.acquire(actor, state.identity.publication_id)
    with pytest.raises(ValueError, match='capture_not_finalized'):
        responses.prepare(actor, lease)
    state = finalized(journal, actor, state, lease)
    original = responses.prepare(actor, lease)
    assert original == responses.prepare(actor, lease)
    payload = SupervisionResponse.model_validate_json(json.dumps(json.loads(original.command.canonical_bytes)['payload']))
    owner_receipt = receipt(original.command, payload)
    observed = RecordingObservation.observe(original.command, owner_receipt)
    pending = responses.record(actor, lease, 0, observed)
    assert pending.observation.status == 'awaiting_readback'
    verified = RecordingObservation.observe(original.command, owner_receipt, readback=payload, previous=observed)
    done = responses.record(actor, lease, 1, verified)
    assert done.observation.status == 'recorded'
    assert responses.record(actor, lease, 0, verified) == done
    journal.release(actor, lease)
    reader = replace(actor, actions=frozenset({'read_attempts'}))
    replacement = CaptureJournal(stored.engine, 'data-owner')
    assert replacement.read(reader, state.identity.publication_id) == state
    assert CaptureResponseJournal(replacement).read(reader, state.identity.publication_id) == done
    with pytest.raises(PermissionError):
        replacement.acquire(reader, state.identity.publication_id)
    with pytest.raises(ValueError, match='capture_configuration_conflict'):
        CaptureJournal(stored.engine, 'different-owner').register(actor, capture)


def test_concurrent_registration_and_lease_have_one_original_winner(stored, capture):
    journal = CaptureJournal(stored.engine, 'data-owner')
    barrier = Barrier(2)
    def register():
        barrier.wait(10)
        return journal.register(stored.principal, capture)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(register) for _ in range(2)]
        first, second = [f.result(20) for f in futures]
    assert first == second
    lease = journal.acquire(stored.principal, first.identity.publication_id)
    with pytest.raises(ValueError, match='capture_lease_unavailable'):
        journal.acquire(stored.principal, first.identity.publication_id)
    journal.release(stored.principal, lease)
    lease = journal.acquire(stored.principal, first.identity.publication_id, seconds=1)
    time.sleep(1.1)
    current = journal.acquire(stored.principal, first.identity.publication_id)
    assert current.fence == lease.fence + 1
    for operation in (lambda: journal.guard(stored.principal, lease), lambda: journal.release(stored.principal, lease),
        lambda: journal.advance(stored.principal, lease, 1, 'rejected', {'reason': 'denied'})):
        with pytest.raises(ValueError, match='capture_lease_lost'):
            operation()
    journal.release(stored.principal, current)


def test_registration_rolls_back_identity_control_and_initial_event(stored, capture, monkeypatch):
    journal = CaptureJournal(stored.engine, 'data-owner')
    original = journal._event
    def fail(*args):
        original(*args)
        raise RuntimeError('after-insert')
    monkeypatch.setattr(journal, '_event', fail)
    with pytest.raises(RuntimeError, match='after-insert'):
        journal.register(stored.principal, capture)
    with stored.engine.connect() as conn:
        for table in ('capture_publications', 'capture_publication_control', 'capture_publication_events'):
            assert conn.execute(text('SELECT count(*) FROM planning.' + table + ' WHERE project_id=:project'),
                {'project': stored.principal.scope.project_id}).scalar_one() == 0
    monkeypatch.setattr(journal, '_event', original)
    state = journal.register(stored.principal, capture)
    lease = journal.acquire(stored.principal, state.identity.publication_id)
    rejected = journal.advance(stored.principal, lease, 1, 'rejected', {'reason': 'denied'})
    with pytest.raises(ValueError, match='capture_position_conflict'):
        journal.advance(stored.principal, lease, 1, 'rejected', {'reason': 'other'})
    assert journal.read(stored.principal, state.identity.publication_id) == rejected


def test_history_is_insert_only_and_unknown_late_is_not_invented(stored, capture):
    journal = CaptureJournal(stored.engine, 'data-owner')
    state = journal.register(stored.principal, capture)
    with pytest.raises(ValueError, match='capture_late_missing'):
        journal.register(stored.principal, capture, kind='late')
    for table in ('capture_publications', 'capture_publication_events', 'capture_response_commands', 'capture_response_observations'):
        with pytest.raises(DBAPIError), stored.engine.begin() as conn:
            conn.execute(text('DELETE FROM planning.' + table))
    assert journal.read(stored.principal, state.identity.publication_id) == state


def expired_with_late(stored):
    from amphora_agent_planning.context import AttemptBinding
    from amphora_agent_planning.persistence.budget import BudgetLedger
    from amphora_agent_planning.persistence.dispatch import DispatchJournal
    from amphora_agent_planning.persistence.settlement import SettlementJournal
    from amphora_agent_planning.providers import observe
    from amphora_agent_planning.supervision_execution.packet import CheckpointProvider
    worker, _, provider, intake = setup(stored)
    packet = worker._packet(stored.principal, intake)
    binding = AttemptBinding(intake.planning, 1)
    BudgetLedger(stored.engine).reserve(stored.principal, binding, packet.context.budget_policy(worker.templates))
    dispatch = DispatchJournal(stored.engine)
    ticket = dispatch.issue(stored.principal, binding, 1)
    time.sleep(1.1)
    dispatch.recover(stored.principal, binding)
    SettlementJournal(stored.engine).settle(stored.principal, binding)
    # Script a response that was in flight when the durable ticket expired.
    late = observe(binding, CheckpointProvider(provider, packet, lambda _: intake.document().deadline_unix_ms))
    dispatch.complete(stored.principal, binding, ticket, late)
    return binding.reference()


def test_empty_primary_and_nonempty_late_publish_in_distinct_slots(stored):
    attempt = expired_with_late(stored)
    journal = CaptureJournal(stored.engine, 'data-owner')
    primary = journal.register(stored.principal, attempt)
    late = journal.register(stored.principal, attempt, kind='late')
    assert primary.position == 0 and primary.payload is None and primary.attempt is None
    assert late.position == 1 and late.payload is not None
    assert primary.identity.publication_id != late.identity.publication_id
    lease = journal.acquire(stored.principal, primary.identity.publication_id)
    responses = CaptureResponseJournal(journal)
    command = responses.prepare(stored.principal, lease).command
    payload = json.loads(command.canonical_bytes)['payload']
    assert payload['capture'] is None and payload['observation']['status'] == 'unknown'
    assert journal.register(stored.principal, attempt) == primary
    assert journal.register(stored.principal, attempt, kind='late') == late


def test_command_insert_rolls_back_when_lease_expires_at_final_guard(stored, monkeypatch):
    attempt = expired_with_late(stored)
    journal = CaptureJournal(stored.engine, 'data-owner')
    state = journal.register(stored.principal, attempt)
    responses = CaptureResponseJournal(journal)
    lease = journal.acquire(stored.principal, state.identity.publication_id, seconds=1)
    original, entered = responses._command, []
    def delayed(*args):
        command = original(*args)
        entered.append(True)
        time.sleep(1.1)
        return command
    monkeypatch.setattr(responses, '_command', delayed)
    with pytest.raises(ValueError, match='capture_lease_lost'):
        responses.prepare(stored.principal, lease)
    assert entered
    assert responses.read(stored.principal, state.identity.publication_id).command is None


def test_response_conflicts_do_not_overwrite_original_receipt(stored):
    attempt = expired_with_late(stored)
    journal = CaptureJournal(stored.engine, 'data-owner')
    state = journal.register(stored.principal, attempt)
    lease = journal.acquire(stored.principal, state.identity.publication_id)
    responses = CaptureResponseJournal(journal)
    command = responses.prepare(stored.principal, lease).command
    payload = SupervisionResponse.model_validate_json(json.dumps(json.loads(command.canonical_bytes)['payload']))
    pending = RecordingObservation.observe(command, receipt(command, payload, 'pending'))
    original = responses.record(stored.principal, lease, 0, pending)
    recorded = RecordingObservation.observe(command, receipt(command, payload), previous=pending)
    with pytest.raises(ValueError, match='capture_response_position_conflict'):
        responses.record(stored.principal, lease, 0, recorded)
    assert responses.read(stored.principal, state.identity.publication_id) == original
    done = responses.record(stored.principal, lease, 1, recorded)
    with pytest.raises(ValueError, match='terminal_receipt_changed'):
        responses.record(stored.principal, lease, 2, pending)
    assert responses.read(stored.principal, state.identity.publication_id) == done


def test_upload_event_rolls_back_at_expired_final_position_fence(stored, capture, monkeypatch):
    journal = CaptureJournal(stored.engine, 'data-owner')
    state = journal.register(stored.principal, capture)
    lease = journal.acquire(stored.principal, state.identity.publication_id, seconds=1)
    original, entered = journal._event, []
    def delayed(*args):
        original(*args)
        entered.append(True)
        time.sleep(1.1)
    monkeypatch.setattr(journal, '_event', delayed)
    with pytest.raises(ValueError, match='capture_lease_or_position_lost'):
        journal.advance(stored.principal, lease, 1, 'rejected', {'reason': 'denied'})
    assert entered
    assert journal.read(stored.principal, state.identity.publication_id) == state


def test_copied_event_cannot_fabricate_a_second_position(stored, capture):
    journal = CaptureJournal(stored.engine, 'data-owner')
    state = journal.register(stored.principal, capture)
    params = {'tenant': stored.principal.scope.tenant_id, 'project': stored.principal.scope.project_id,
              'publication': state.identity.publication_id}
    event = state.events[0][0]
    with stored.engine.begin() as conn:
        journal._event(conn, params, 2, event)
        conn.execute(text('UPDATE planning.capture_publication_control SET position=2 WHERE '
            'tenant_id=:tenant AND project_id=:project AND publication_id=:publication'), params)
    with pytest.raises(ValueError, match='stored_publication_event'):
        journal.read(stored.principal, state.identity.publication_id)
