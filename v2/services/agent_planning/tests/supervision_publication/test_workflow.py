"""Real Planning SQL and SDK/client routes with scripted Data and HTTP Runtime."""

import pytest
from amphora_agent_planning.supervision_client import ExchangeUnavailable
from amphora_agent_planning.supervision_publication.exchange import (
    CaptureResponseJournal,
)
from amphora_agent_planning.supervision_publication.journal import CaptureJournal
from amphora_agent_planning.supervision_publication.workflow import (
    CapturePublisher,
    CaptureResponder,
    release,
)
from amphora_tool_protocol import (
    ArtifactClient,
    CommandUnresolved,
    TransportLost,
    WorkerIdentity,
)

from ..publication.test_workflow import DataPeer
from .runtime_peer import RuntimePeer
from .test_journal import capture as capture  # noqa: PLC0414 - pytest fixture re-export
from .test_journal import expired_with_late

pytestmark = pytest.mark.postgres


def publisher(stored, capture):
    journal = CaptureJournal(stored.engine, 'data-owner')
    state = journal.register(stored.principal, capture)
    peer = DataPeer(state.identity, state.payload.artifact)
    client = ArtifactClient(peer, WorkerIdentity(stored.principal.actor_id, stored.principal.scope))
    return CapturePublisher(journal, client), peer


@pytest.mark.parametrize('lost', ['begin', 'stream', 'finalize', 'none'])
def test_sdk_upload_recovery_retains_original_bytes(stored, capture, lost):
    pub, peer = publisher(stored, capture)
    peer.lost_begin = lost == 'begin'
    peer.lost_put = lost == 'stream'
    peer.lost_finalize = lost == 'finalize'
    if lost in {'stream', 'finalize'}:
        with pytest.raises(CommandUnresolved if lost == 'finalize' else TransportLost):
            pub.publish(stored.principal, capture)
        peer.lost_put = peer.lost_finalize = peer.final_lookup_down = False
    state = pub.publish(stored.principal, capture)
    assert state.attempt.stage == 'finalized'
    assert state.attempt.identity.ordinal == (2 if lost == 'stream' else 1)
    assert state.attempt.result.artifact.sha256 == state.origin.observation.capture.sha256
    calls = len(peer.calls)
    replacement = CapturePublisher(CaptureJournal(stored.engine, 'data-owner'), None)
    assert replacement.publish(stored.principal, capture) == state
    assert len(peer.calls) == calls
    if lost == 'finalize':
        assert sum(method == 'POST' and path == '/v1/artifacts/finalize' for method, path, _ in peer.calls) == 1


def test_data_rejection_retains_capture_and_is_not_a_success_response(stored, capture):
    pub, peer = publisher(stored, capture)
    peer.reject = True
    state = pub.publish(stored.principal, capture)
    assert state.attempt.stage == 'rejected' and state.origin.observation.capture.content
    with RuntimePeer(stored.principal) as runtime:
        sender = CaptureResponder(CaptureResponseJournal(pub.journal), runtime.client)
        with pytest.raises(ValueError, match='capture_not_finalized'):
            sender.send(stored.principal, state.identity.publication_id)
        assert not runtime.calls


@pytest.mark.parametrize('loss', ['write', 'readback', 'none'])
def test_http_response_loss_recovers_original_without_second_write(stored, capture, loss):
    pub, _ = publisher(stored, capture)
    state = pub.publish(stored.principal, capture)
    responses = CaptureResponseJournal(pub.journal)
    with RuntimePeer(stored.principal) as runtime:
        runtime.drop_write = loss == 'write'
        runtime.readback_down = loss == 'readback'
        sender = CaptureResponder(responses, runtime.client)
        if loss != 'none':
            with pytest.raises(ExchangeUnavailable):
                sender.send(stored.principal, state.identity.publication_id)
            retained = responses.read(stored.principal, state.identity.publication_id)
            assert retained.command == runtime.command
            if loss == 'readback':
                assert retained.observation.status == 'awaiting_readback'
            runtime.readback_down = False
        done = sender.send(stored.principal, state.identity.publication_id)
        assert done.observation.status == 'recorded'
        assert sum(path == '/v1/supervision/responses' for _, path, _ in runtime.calls) == 1
        calls = len(runtime.calls)
        replacement = CaptureResponder(CaptureResponseJournal(CaptureJournal(stored.engine, 'data-owner')), None)
        assert replacement.send(stored.principal, state.identity.publication_id) == done
        assert len(runtime.calls) == calls


def test_empty_capture_skips_data_and_disappeared_known_receipt_never_reposts(stored):
    attempt = expired_with_late(stored)
    journal = CaptureJournal(stored.engine, 'data-owner')
    state = CapturePublisher(journal, None).publish(stored.principal, attempt)
    assert state.payload is None
    with RuntimePeer(stored.principal) as runtime:
        runtime.outcome = 'pending'
        sender = CaptureResponder(CaptureResponseJournal(journal), runtime.client)
        pending = sender.send(stored.principal, state.identity.publication_id)
        assert pending.observation.status == 'pending'
        runtime.disappear = True
        with pytest.raises(ExchangeUnavailable, match='capture_receipt_disappeared'):
            sender.send(stored.principal, state.identity.publication_id)
        assert sum(path == '/v1/supervision/responses' for _, path, _ in runtime.calls) == 1


@pytest.mark.parametrize('reason', ['capture_lease_lost', 'unexpected_storage_failure'])
def test_release_never_hides_unrelated_storage_failure(reason):
    class Journal:
        def release(self, *_args):
            raise ValueError(reason)
    if reason == 'capture_lease_lost':
        release(Journal(), None, None)
    else:
        with pytest.raises(ValueError, match=reason):
            release(Journal(), None, None)


def test_wrong_configured_actor_cannot_publish_or_send(stored, capture):
    pub, peer = publisher(stored, capture)
    pub.client.identity = WorkerIdentity('wrong-actor', stored.principal.scope)
    with pytest.raises(ValueError, match='capture_publication_client'):
        pub.publish(stored.principal, capture)
    assert not peer.calls
    pub.client.identity = WorkerIdentity(stored.principal.actor_id, stored.principal.scope)
    state = pub.publish(stored.principal, capture)
    with RuntimePeer(stored.principal) as runtime:
        runtime.client.actor_id = 'wrong-actor'
        with pytest.raises(ValueError, match='capture_response_client'):
            CaptureResponder(CaptureResponseJournal(pub.journal), runtime.client).send(
                stored.principal, state.identity.publication_id)
        assert not runtime.calls
