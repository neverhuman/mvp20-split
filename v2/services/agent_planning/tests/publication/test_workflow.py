"""Actual owner journal plus public SDK against a scripted Data boundary."""

import json
from dataclasses import replace

import pytest
from amphora_agent_planning.publication import AttemptIdentity, PublicationAttempt
from amphora_agent_planning.publication.workflow import TracePublisher
from amphora_tool_protocol import (
    ArtifactClient,
    Reply,
    TransportLost,
    WorkerIdentity,
)

from .test_journal import setup
from .test_values import receipts

pytestmark = pytest.mark.postgres


def encoded(value):
    return json.dumps(value).encode()


class DataPeer:
    def __init__(self, identity, artifact):
        self.identity, self.artifact = identity, artifact
        self.calls, self.commands, self.uploads = [], {}, {}
        self.lost_begin = self.lost_put = self.lost_finalize = self.final_lookup_down = False
        self.derivation_down = self.forge = self.reject = False
        self.after_put = lambda: None

    def request(self, method, path, body=None, **kwargs):
        self.calls.append((method, path, body))
        if path.startswith('/v1/commands/'):
            family, key = path.split('/')[-2:]
            if family == 'artifacts.finalize' and self.final_lookup_down:
                return Reply(503, b'')
            return Reply(200, self.commands[key]) if key in self.commands else Reply(404, b'')
        if method == 'POST':
            command = json.loads(body)
            key, family = command['identity']['command_id'], command['identity']['command_family']
            if family == 'artifacts.begin_derived_upload':
                ordinal = next(i for i in range(1, 9) if AttemptIdentity.for_publication(self.identity, i).begin_id == key)
                attempt = PublicationAttempt(AttemptIdentity.for_publication(self.identity, ordinal))
                assert attempt.begin_command(self.identity, self.artifact).canonical_bytes == body
                upload, stream, final, derivation = receipts(self.identity, self.artifact, attempt)
                # Only newly allocated output/upload identities change. Inputs
                # named "output" remain exact immutable derivation references.
                values = [v.model_dump(mode='json') for v in (upload, stream, final, derivation)]
                values[0]['upload']['upload_id'] = 'upload-' + str(ordinal)
                for value in values[1:]:
                    value['upload_id'] = 'upload-' + str(ordinal)
                for value in values[2:]:
                    value['artifact']['artifact_id'] = 'output-' + str(ordinal)
                self.uploads['upload-' + str(ordinal)] = values
                outcome = {'status': 'derived_uploaded', 'receipt': values[0]}
                response = values[0]
                digest = attempt.begin_command(self.identity, self.artifact).sha256
            else:
                values = self.uploads[command['payload']['upload_id']]
                ordinal = int(command['payload']['upload_id'].split('-')[-1])
                attempt = PublicationAttempt(AttemptIdentity.for_publication(self.identity, ordinal))
                from amphora_contracts_artifacts import DerivedUploadReceipt
                attempt = attempt.begun(self.identity, self.artifact, DerivedUploadReceipt.model_validate_json(encoded(values[0])))
                attempt = replace(attempt, stage='finalizing')
                assert attempt.finalize_command(self.identity).canonical_bytes == body
                outcome = {'status': 'finalized', 'receipt': values[2]}
                response, digest = values[2], attempt.finalize_command(self.identity).sha256
            if self.reject:
                outcome = {'status': 'rejected', 'reason_code': 'source_process_denied'}
            observation = {'identity': command['identity'], 'operation_id': key,
                           'request_sha256': digest, 'outcome': outcome}
            self.commands[key] = encoded(observation)
            if self.reject:
                return Reply(409, b'')
            if family == 'artifacts.begin_derived_upload' and self.lost_begin:
                self.lost_begin = False
                raise TransportLost('scripted_loss')
            if family == 'artifacts.finalize' and self.lost_finalize:
                self.final_lookup_down = True
                raise TransportLost('scripted_loss')
            return Reply(200, encoded(response))
        if method == 'PUT':
            assert body == self.artifact.body
            self.after_put()
            if self.lost_put:
                raise TransportLost('scripted_loss')
            return Reply(200, encoded(self.uploads[path.split('/')[3]][1]))
        assert method == 'GET' and path.endswith('/derivation')
        if self.derivation_down:
            return Reply(503, b'')
        value = next(v[3].copy() for v in self.uploads.values() if v[3]['artifact']['artifact_id'] == path.split('/')[3])
        if self.forge:
            value['request_sha256'] = 'f' * 64
        return Reply(200, encoded(value))


class Reviewer:
    def __init__(self, review):
        self.result, self.calls = review, 0

    def review(self, task):
        assert task == self.result.task
        self.calls += 1
        return self.result


def workflow(s):
    store, journal, identity, review, artifact = setup(s)
    peer, reviewer = DataPeer(identity, artifact), Reviewer(review)
    publisher = TracePublisher(journal, reviewer, ArtifactClient(peer, WorkerIdentity(s.principal.actor_id, s.principal.scope)))
    return publisher, peer, reviewer, identity, store, journal


def test_sdk_commands_exact_and_lost_begin_reconciles_without_duplicate_upload(stored):
    publisher, peer, reviewer, identity, _store, journal = workflow(stored)
    peer.lost_begin = True
    result = publisher.publish(stored.principal, 'publication', identity.trace())
    assert result.attempt.stage == 'finalized' and result.position == 6
    assert reviewer.calls == 1 and len(peer.uploads) == 1
    assert [method for method, _, _ in peer.calls].count('PUT') == 1
    calls = list(peer.calls)
    assert publisher.publish(stored.principal, 'publication', identity.trace()) == result
    assert peer.calls == calls and reviewer.calls == 1
    assert journal.read(stored.principal, 'publication') == result


def test_lost_put_preserved_then_replaced_never_repeated(stored):
    publisher, peer, reviewer, identity, _store, journal = workflow(stored)
    peer.lost_put = True
    with pytest.raises(TransportLost):
        publisher.publish(stored.principal, 'publication', identity.trace())
    first = journal.read(stored.principal, 'publication')
    assert first.attempt.stage == 'streaming'
    peer.lost_put = False
    result = publisher.publish(stored.principal, 'publication', identity.trace())
    assert result.attempt.stage == 'finalized' and result.attempt.identity.ordinal == 2
    assert [path for method, path, _ in peer.calls if method == 'PUT'] == [
        '/v1/uploads/upload-1/content', '/v1/uploads/upload-2/content']
    assert [json.loads(e.canonical)['action'] for e, _ in result.events][:5] == [
        'prepared', 'begun', 'streaming', 'abandoned', 'replacement']
    assert reviewer.calls == 1  # Stored metadata is replayed, never asserted to be fresh authorization.


@pytest.mark.parametrize('failure', ['finalize', 'derivation', 'forged_derivation'])
def test_uncertain_finalization_preserves_command_and_never_restreams(stored, failure):
    publisher, peer, _reviewer, identity, _store, journal = workflow(stored)
    peer.lost_finalize = failure == 'finalize'
    peer.derivation_down = failure == 'derivation'
    peer.forge = failure == 'forged_derivation'
    with pytest.raises(ValueError):
        publisher.publish(stored.principal, 'publication', identity.trace())
    state = journal.read(stored.principal, 'publication')
    assert state.attempt.stage == 'finalizing'
    key = state.attempt.identity.finalize_id
    peer.lost_finalize = peer.final_lookup_down = peer.derivation_down = peer.forge = False
    result = publisher.publish(stored.principal, 'publication', identity.trace())
    assert result.attempt.stage == 'finalized' and result.attempt.identity.finalize_id == key
    assert len([1 for method, _, _ in peer.calls if method == 'PUT']) == 1
    assert len([1 for method, path, _ in peer.calls if method == 'POST' and path.endswith('finalize')]) == 1


@pytest.mark.parametrize('stage', ['begin', 'finalize'])
def test_durable_rejection_is_terminal_and_replay_does_not_call_peer(stored, stage):
    publisher, peer, _reviewer, identity, _store, _journal = workflow(stored)
    if stage == 'begin':
        peer.reject = True
    else:
        peer.after_put = lambda: setattr(peer, 'reject', True)
    state = publisher.publish(stored.principal, 'publication', identity.trace())
    assert state.attempt.stage == 'rejected' and state.attempt.rejection == 'source_process_denied'
    calls = len(peer.calls)
    assert publisher.publish(stored.principal, 'publication', identity.trace()) == state
    assert len(peer.calls) == calls


def test_foreign_client_denied_before_journal_or_peer_and_source_failure_retains_empty_intent(stored):
    publisher, peer, reviewer, identity, store, journal = workflow(stored)
    publisher.client.identity = WorkerIdentity('different', stored.principal.scope)
    with pytest.raises(ValueError, match='publication_client_identity'):
        publisher.publish(stored.principal, 'publication', identity.trace())
    assert not peer.calls
    publisher.client.identity = WorkerIdentity(stored.principal.actor_id, stored.principal.scope)
    def denied(task):
        raise ValueError('source_access_denied')
    reviewer.review = denied
    with pytest.raises(ValueError, match='source_access_denied'):
        publisher.publish(stored.principal, 'publication', identity.trace())
    assert journal.read(stored.principal, 'publication').position == 0 and not peer.calls
    lease = store.acquire(stored.principal, 'publication')
    store.release(stored.principal, lease)


def test_lease_loss_after_put_never_records_success_or_finalizes(stored):
    publisher, peer, _reviewer, identity, store, journal = workflow(stored)
    original = store.acquire
    leases = []
    def acquire(*args, **kwargs):
        lease = original(*args, **kwargs)
        leases.append(lease)
        return lease
    store.acquire = acquire
    peer.after_put = lambda: store.release(stored.principal, leases[-1])
    with pytest.raises(ValueError, match='publication_lease_lost'):
        publisher.publish(stored.principal, 'publication', identity.trace())
    assert journal.read(stored.principal, 'publication').attempt.stage == 'streaming'
    assert not any(path.endswith('/finalize') for _, path, _ in peer.calls)
    peer.after_put = lambda: None
    assert publisher.publish(stored.principal, 'publication', identity.trace()).attempt.identity.ordinal == 2


def test_eight_uncertain_uploads_bound_recovery_without_ninth_effect(stored):
    publisher, peer, _reviewer, identity, _store, journal = workflow(stored)
    peer.lost_put = True
    for _ in range(8):
        with pytest.raises(TransportLost):
            publisher.publish(stored.principal, 'publication', identity.trace())
    with pytest.raises(ValueError, match='publication_attempt_limit'):
        publisher.publish(stored.principal, 'publication', identity.trace())
    state = journal.read(stored.principal, 'publication')
    assert state.attempt.stage == 'abandoned' and state.attempt.identity.ordinal == 8
    assert len(peer.uploads) == 8 and state.position <= 64


@pytest.mark.parametrize('boundary', ['prepared', 'begun', 'streaming', 'streamed', 'finalizing', 'finalized'])
def test_exception_after_committed_transition_resumes_from_history(stored, boundary):
    publisher, peer, _reviewer, identity, _store, journal = workflow(stored)
    original_prepare, original_advance = journal.prepare, journal.advance
    def fail_after(state):
        if state.attempt.stage == boundary:
            raise RuntimeError('injected_after_commit')
        return state
    journal.prepare = lambda *args, **kwargs: fail_after(original_prepare(*args, **kwargs))
    journal.advance = lambda *args, **kwargs: fail_after(original_advance(*args, **kwargs))
    with pytest.raises(RuntimeError, match='injected_after_commit'):
        publisher.publish(stored.principal, 'publication', identity.trace())
    retained = journal.read(stored.principal, 'publication')
    assert retained.attempt.stage == boundary
    journal.prepare, journal.advance = original_prepare, original_advance
    result = publisher.publish(stored.principal, 'publication', identity.trace())
    assert result.attempt.stage == 'finalized'
    assert result.events[:len(retained.events)] == retained.events
    puts = [path for method, path, _ in peer.calls if method == 'PUT']
    assert len(puts) == len(set(puts)) == 1
    assert result.attempt.identity.ordinal == (2 if boundary == 'streaming' else 1)


@pytest.mark.parametrize('status', [403, 503])
def test_unknown_or_denied_begin_lookup_never_blindly_submits(stored, status):
    publisher, peer, _reviewer, identity, _store, journal = workflow(stored)
    calls = []
    def unavailable(method, path, body=None, **kwargs):
        calls.append((method, path))
        return Reply(status, b'')
    peer.request = unavailable
    with pytest.raises(ValueError):
        publisher.publish(stored.principal, 'publication', identity.trace())
    assert journal.read(stored.principal, 'publication').attempt.stage == 'prepared'
    assert all(method == 'GET' for method, _ in calls) and 1 <= len(calls) <= 3
