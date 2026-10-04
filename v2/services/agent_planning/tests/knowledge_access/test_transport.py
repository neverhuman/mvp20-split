import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from amphora_agent_planning.knowledge_access import KnowledgeReadWindow, KnowledgeTransport

from .test_reader import inputs


@pytest.fixture
def peer():
    task, scripted, _ = inputs()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            self.server.calls.append((self.path, self.headers.get('Authorization'), json.loads(body)))
            try:
                if self.server.trickle_headers:
                    self.connection.sendall(b'HTTP/1.1 200 OK\r\nX-Slow: ')
                    for _ in range(30):
                        self.connection.sendall(b'x')
                        time.sleep(0.02)
                    return
                self.send_response(self.server.status)
                self.send_header('Content-Type', self.server.media)
                self.send_header('Content-Length', str(len(self.server.body)))
                self.end_headers()
                if self.server.trickle:
                    for byte in self.server.body:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.02)
                else:
                    self.wfile.write(self.server.body)
            except OSError:
                pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    server.calls, server.status, server.media = [], 200, 'application/json'
    server.body = scripted.records['/v1/graph-profiles/read'].model_dump_json().encode()
    server.trickle = server.trickle_headers = False
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
    thread.start()
    transport = KnowledgeTransport(f'http://127.0.0.1:{server.server_port}', 't' * 32)
    yield server, transport, task.document().target.graph
    server.shutdown()
    server.server_close()
    thread.join(2)


def test_exact_authenticated_post_and_window_accounting(peer):
    server, transport, graph = peer
    window = KnowledgeReadWindow()
    assert transport.read('/v1/graph-profiles/read', graph, window).graph == graph
    assert server.calls == [('/v1/graph-profiles/read', 'Bearer ' + 't' * 32, graph.model_dump(mode='json'))]
    assert window.calls == 1 and window.consumed == len(server.body)


@pytest.mark.parametrize('status,reason', [(401, 'knowledge_access_denied'), (403, 'knowledge_access_denied'),
    (404, 'knowledge_reference_unavailable'), (302, 'knowledge_peer_unavailable'), (503, 'knowledge_peer_unavailable')])
def test_status_has_no_fallback_or_retry(peer, status, reason):
    server, transport, graph = peer
    server.status = status
    server.body = b'SECRET peer error body'
    with pytest.raises(ValueError, match='^' + reason + '$'):
        transport.read('/v1/graph-profiles/read', graph, KnowledgeReadWindow())
    assert len(server.calls) == 1


@pytest.mark.parametrize('body', [b'null', b'{}', b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff'])
def test_malformed_or_foreign_json_is_not_owner_context(peer, body):
    server, transport, graph = peer
    server.body = body
    with pytest.raises(ValueError, match='knowledge_peer_protocol'):
        transport.read('/v1/graph-profiles/read', graph, KnowledgeReadWindow())


def test_media_size_and_route_bounds(peer):
    server, transport, graph = peer
    server.media = 'text/plain'
    with pytest.raises(ValueError, match='knowledge_peer_media'):
        transport.read('/v1/graph-profiles/read', graph, KnowledgeReadWindow())
    server.media, server.body = 'application/json', b'x' * 262145
    with pytest.raises(ValueError, match='knowledge_response_limit'):
        transport.read('/v1/graph-profiles/read', graph, KnowledgeReadWindow())
    with pytest.raises(ValueError, match='knowledge_peer_path'):
        transport.read('/v1/graph-proposals', graph, KnowledgeReadWindow())
    assert len(server.calls) == 2


@pytest.mark.parametrize('kind', ['trickle', 'trickle_headers'])
def test_whole_read_deadline_bounds_trickling_headers_and_body(peer, kind):
    server, transport, graph = peer
    setattr(server, kind, True)
    start = time.monotonic()
    with pytest.raises(ValueError, match='knowledge_(read_expired|peer_unavailable)'):
        transport.read('/v1/graph-profiles/read', graph, KnowledgeReadWindow(seconds=0.12))
    assert time.monotonic() - start < 1


@pytest.mark.parametrize('endpoint', ['https://127.0.0.1:1', 'http://localhost:1', 'http://127.0.0.1',
    'http://user@127.0.0.1:1', 'http://127.0.0.1:1/path', 'http://127.0.0.1:99999'])
def test_endpoint_configuration_is_explicit_and_loopback_only(endpoint):
    with pytest.raises(ValueError, match='knowledge_peer_endpoint'):
        KnowledgeTransport(endpoint, 't' * 32)


def test_window_cannot_extend_or_reset_call_and_byte_ceilings():
    window = KnowledgeReadWindow()
    for _ in range(3):
        window.start()
    with pytest.raises(ValueError, match='knowledge_read_call_limit'):
        window.start()
    with pytest.raises(ValueError, match='knowledge_read_byte_limit'):
        window.consume(18087937)
    with pytest.raises(ValueError, match='knowledge_read_deadline'):
        KnowledgeReadWindow(seconds=True)
