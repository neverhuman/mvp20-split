import http.client
import pytest

from amphora_deployment.campaign_launch.intent import LaunchError
from amphora_deployment.campaign_launch.ports import PeerUnavailable
from amphora_deployment.campaign_launch.runtime_peer import RuntimePeer


@pytest.fixture
def peer(monkeypatch):
    class Connection:
        status = 200
        body = b'{}'
        calls = []
        closed = 0
        def __init__(self, host, port, timeout):
            assert (host, port, timeout) == ('127.0.0.1', 57018, 5)
        def request(self, *args): self.calls.append(args)
        def getresponse(self): return self
        def read(self, maximum): return self.body[:maximum]
        def close(self): type(self).closed += 1
    monkeypatch.setattr(http.client, 'HTTPConnection', Connection)
    return RuntimePeer(57018, 'secret-test-token'), Connection


def test_admission_sends_exact_canonical_bytes_and_bound_credential(peer, make_intent, admission_receipt):
    client, connection = peer
    intent = make_intent()
    connection.body = admission_receipt(intent).model_dump_json().encode()
    assert client.admit(intent) == admission_receipt(intent)
    method, route, raw, headers = connection.calls[0]
    assert (method, route, raw) == ('POST', '/v1/graph-runs/drafts', intent.admission.canonical_bytes)
    assert headers['Authorization'] == 'Bearer secret-test-token'
    assert connection.closed == 1


def test_receipt_missing_is_explicit_and_actor_scoped(peer, make_intent):
    client, connection = peer
    connection.status, connection.body = 404, b'{"reason_code":"receipt_unavailable","resnapshot":false}'
    assert client.receipt(make_intent()) is None
    assert connection.calls[0][1] == '/v1/commands/graph.admit_draft/launch-1?actor_id=researcher'


@pytest.mark.parametrize('status,body', [(404, b'{}'), (404, b'{"reason_code":"command_unavailable"}'),
    (200, b'{}'), (302, b'{}'), (401, b'{}'), (403, b'{}'), (200, b'x' * 262145)],
    ids=['unknown-missing', 'wrong-family', 'malformed', 'redirect', 'unauthenticated', 'denied', 'oversize'])
def test_bad_responses_cannot_be_mistaken_for_missing_or_rejection(peer, make_intent, status, body):
    client, connection = peer
    connection.status, connection.body = status, body
    with pytest.raises(LaunchError, match='launch_peer_response_invalid'):
        client.receipt(make_intent())
    assert connection.closed == 1


@pytest.mark.parametrize('status', [408, 425, 429, 500, 503])
def test_transient_http_failure_remains_ambiguous(peer, make_intent, status):
    client, connection = peer
    connection.status = status
    with pytest.raises(PeerUnavailable): client.admit(make_intent())


def test_network_exception_never_leaks_credential_or_request(peer, make_intent):
    client, connection = peer
    def fail(self): raise OSError('private token payload')
    connection.getresponse = fail
    with pytest.raises(PeerUnavailable) as error: client.admit(make_intent())
    assert str(error.value) == '' and connection.closed == 1
