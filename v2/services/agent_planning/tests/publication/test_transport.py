"""Publication SDK transport over actual scripted loopback sockets."""

import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from amphora_agent_planning.publication.transport import PublicationTransport
from amphora_tool_protocol import ProtocolError, TransportLost


@pytest.fixture
def peer():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def handle_request(self):
            self.server.calls.append((self.command, self.path, self.headers.get('Authorization'),
                                      self.rfile.read(int(self.headers.get('Content-Length', 0)))))
            try:
                if self.server.mode == 'headers':
                    self.connection.sendall(b'HTTP/1.1 200 OK\r\nX-Slow: ')
                    for _ in range(30):
                        self.connection.sendall(b'x')
                        time.sleep(0.03)
                    return
                self.send_response(self.server.status)
                self.send_header('Content-Type', self.server.media)
                self.send_header('Content-Length', str(len(self.server.body)))
                self.end_headers()
                for byte in self.server.body:
                    self.wfile.write(bytes([byte]))
                    if self.server.mode == 'body':
                        self.wfile.flush()
                        time.sleep(0.03)
            except OSError:
                pass

        do_GET = do_POST = do_PUT = handle_request

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    server.calls, server.status, server.media = [], 200, 'application/json'
    server.body, server.mode = b'{"result":"ok"}', 'normal'
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
    thread.start()
    endpoint = f'http://127.0.0.1:{server.server_port}'
    yield server, endpoint
    server.shutdown()
    server.server_close()
    thread.join(2)


def test_closed_routes_authenticated_single_exchange_and_statuses(peer):
    server, endpoint = peer
    client = PublicationTransport(endpoint, 't' * 32)
    for method, path, body in [('GET', '/v1/commands/artifacts.begin_derived_upload/c', None),
                              ('GET', '/v1/commands/artifacts.finalize/c', None),
                              ('GET', '/v1/artifacts/a/derivation', None),
                              ('POST', '/v1/derived-uploads', b'{}'),
                              ('POST', '/v1/artifacts/finalize', b'{}'),
                              ('PUT', '/v1/uploads/u/content', b'{}')]:
        reply = client.request(method, path, body)
        assert reply.status == 200 and reply.body == server.body
        assert server.calls[-1] == (method, path, 'Bearer ' + 't' * 32, body or b'')
    for status in (302, 401, 403, 404, 409, 429, 503):
        server.status, server.body = status, b'private owner diagnostics'
        assert client.request('GET', '/v1/artifacts/a/derivation').status == status
    assert len(server.calls) == 13


@pytest.mark.parametrize('mode', ['headers', 'body'])
def test_trickle_deadline_includes_headers_and_body_without_retry(peer, mode):
    server, endpoint = peer
    server.mode, server.body = mode, b'"' + b'x' * 100 + b'"'
    client = PublicationTransport(endpoint, 't' * 32, seconds=0.12)
    start = time.monotonic()
    with pytest.raises(TransportLost, match='^publication_transport_lost$'):
        client.request('POST', '/v1/derived-uploads', b'{}')
    assert time.monotonic() - start < 1.5 and len(server.calls) == 1


@pytest.mark.parametrize('body', [b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b'{'])
def test_strict_json_prevents_duplicate_or_nonfinite_receipts(peer, body):
    server, endpoint = peer
    server.body = body
    with pytest.raises(ProtocolError, match='publication_response_json'):
        PublicationTransport(endpoint, 't' * 32).request('GET', '/v1/artifacts/a/derivation')


def test_response_bounds_media_and_no_diagnostic_leak(peer):
    server, endpoint = peer
    client = PublicationTransport(endpoint, 't' * 32)
    with pytest.raises(ProtocolError, match='^publication_response_limit$'):
        client.request('GET', '/v1/artifacts/a/derivation', limit=2)
    server.media = 'text/html'
    with pytest.raises(ProtocolError, match='^publication_response_media$'):
        client.request('GET', '/v1/artifacts/a/derivation')
    server.body = b''
    server.status = 404
    assert client.request('GET', '/v1/artifacts/a/derivation', limit=0).body == b''


@pytest.mark.parametrize('endpoint', [None, '', 'https://127.0.0.1:80', 'http://example.com:80',
    'http://localhost:80', 'http://127.0.0.1', 'http://127.0.0.1:bad', 'http://127.0.0.1:0',
    'http://u:p@127.0.0.1:80', 'http://127.0.0.1:80/path', 'http://127.0.0.1:80?x=1'])
def test_endpoint_is_explicit_trusted_local_configuration(endpoint):
    with pytest.raises(ProtocolError, match='publication_endpoint'):
        PublicationTransport(endpoint, 't' * 32)


@pytest.mark.parametrize('kwargs', [{'token': 'short'}, {'token': 'x' * 513}, {'token': 'x' * 31 + '\n'},
    {'seconds': True}, {'seconds': float('nan')}, {'seconds': 0}, {'seconds': 6}])
def test_invalid_credential_or_deadline(kwargs):
    args = {'token': 't' * 32, **kwargs}
    with pytest.raises(ProtocolError):
        PublicationTransport('http://127.0.0.1:80', **args)


def test_invalid_routes_body_and_limits_never_contact_peer(peer):
    server, endpoint = peer
    client = PublicationTransport(endpoint, 't' * 32)
    for method, path, body in [('DELETE', '/v1/derived-uploads', None),
        ('GET', '/v1/artifacts/a/content', None), ('GET', '/v1/artifacts/../a/derivation', None),
        ('POST', '/v1/uploads', b'{}'), ('GET', '/v1/artifacts/a/derivation?x=1', None),
        ('GET', '/v1/artifacts/a/derivation', b'{}'), ('PUT', '/v1/uploads/u/content', None),
        ('PUT', '/v1/uploads/u/content', b'x' * 1048577)]:
        with pytest.raises(ProtocolError):
            client.request(method, path, body)
    for kwargs in ({'limit': True}, {'limit': 262145}, {'media_type': 'x\r\nBad: y'}):
        with pytest.raises(ProtocolError):
            client.request('GET', '/v1/artifacts/a/derivation', **kwargs)
    assert not server.calls


def test_connect_loss_redacted():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    with pytest.raises(TransportLost, match='^publication_transport_lost$'):
        PublicationTransport(f'http://127.0.0.1:{port}', 't' * 32, seconds=0.1).request(
            'GET', '/v1/artifacts/a/derivation')
