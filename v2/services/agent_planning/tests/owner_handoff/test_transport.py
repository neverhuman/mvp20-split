"""Actual loopback exchange limits; scripted owners do not prove registration."""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from amphora_agent_planning.owner_handoff.transport import (
    HandoffWindow,
    OwnerAbsent,
    OwnerConflict,
    OwnerDenied,
    OwnerInvalid,
    OwnerTransport,
    OwnerUnavailable,
)

from .test_values import accepted_fixture, request


@pytest.fixture
def peer():
    value, _ = request()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_): pass
        def handle_request(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.server.calls.append((self.command, self.path, self.headers.get("Authorization"), body))
            try:
                if self.server.trickle_headers:
                    self.connection.sendall(b"HTTP/1.1 200 OK\r\nX-Slow: ")
                    for _ in range(30):
                        self.connection.sendall(b"x")
                        time.sleep(0.02)
                    return
                self.send_response(self.server.status)
                self.send_header("Content-Type", self.server.media)
                self.send_header("Content-Length", str(len(self.server.body)))
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
        do_POST = do_GET = handle_request
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    server.calls, server.status, server.media = [], 200, "application/json"
    server.body = value.canonical
    server.trickle = server.trickle_headers = False
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.server_port}"
    yield server, OwnerTransport("owner", "research", endpoint, "t"*32), value
    server.shutdown()
    server.server_close()
    thread.join(2)


def test_read_and_write_use_distinct_exact_catalog_routes(peer):
    server, transport, value = peer
    window = HandoffWindow()
    assert transport.read(value, window) == value.document()
    assert transport.submit(value, window) == value.document()
    assert [(method, path) for method, path, _, _ in server.calls] == [
        ("POST", "/v1/questions/read"), ("POST", "/v1/questions")]
    assert server.calls[1][3] == value.canonical and server.calls[1][2] == "Bearer " + "t"*32
    assert json.loads(server.calls[0][3]) == value.document().reference.model_dump(mode="json")
    assert window.calls == 2 and window.consumed == 2*len(server.body)


def test_graph_status_submission_and_exact_accepted_read_have_distinct_models(peer):
    server, _, _ = peer
    value, status, accepted = accepted_fixture()
    transport = OwnerTransport("owner", "knowledge", f"http://127.0.0.1:{server.server_port}", "t"*32)
    window = HandoffWindow()
    server.body = status.model_dump_json().encode()
    assert transport.read(value, window) == status
    server.body = status.decision.model_dump_json().encode()
    assert transport.submit(value, window) == status.decision
    server.body = accepted.model_dump_json().encode()
    assert transport.accepted(value, accepted.reference, window) == accepted
    assert server.calls[0][0] == "GET" and not server.calls[0][3]
    assert server.calls[2][1] == "/v1/graph-changes/read"


@pytest.mark.parametrize("write,status,error,reason", [
    (False, 401, OwnerDenied, "handoff_access_denied"), (True, 403, OwnerDenied, "handoff_access_denied"),
    (False, 404, OwnerAbsent, "handoff_reference_absent"), (True, 404, OwnerUnavailable, "handoff_dependency_unavailable"),
    (True, 409, OwnerConflict, "handoff_identity_conflict"), (False, 409, OwnerConflict, "handoff_identity_conflict"),
    (True, 422, OwnerInvalid, "handoff_request_rejected"), (True, 413, OwnerInvalid, "handoff_request_rejected"),
    (False, 302, OwnerUnavailable, "handoff_read_unavailable"), (True, 503, OwnerUnavailable, "handoff_write_uncertain"),
])
def test_statuses_never_retry_or_copy_peer_error_bodies(peer, write, status, error, reason):
    server, transport, value = peer
    server.status, server.body = status, b"PRIVATE peer error body"
    with pytest.raises(error, match="^" + reason + "$"):
        (transport.submit if write else transport.read)(value, HandoffWindow())
    assert len(server.calls) == 1


@pytest.mark.parametrize("body", [b"null", b"{}", b'{"x":1,"x":2}', b'{"x":NaN}', b"\xff"])
def test_malformed_success_is_uncertain_not_acknowledged(peer, body):
    server, transport, value = peer
    server.body = body
    with pytest.raises(OwnerUnavailable, match="handoff_response_protocol"):
        transport.submit(value, HandoffWindow())


def test_response_limits_media_and_wrong_owner_fail_without_fallback(peer):
    server, transport, value = peer
    server.media = "text/plain"
    with pytest.raises(ValueError, match="handoff_response_media"):
        transport.read(value, HandoffWindow())
    server.media, server.body = "application/json", b"x"*262145
    with pytest.raises(ValueError, match="handoff_response_limit"):
        transport.read(value, HandoffWindow())
    graph, _ = request("graph")
    with pytest.raises(ValueError, match="handoff_owner_binding"):
        transport.submit(graph, HandoffWindow())
    assert len(server.calls) == 2


@pytest.mark.parametrize("when", [1, 2])
def test_fence_guard_prevents_send_before_connect_or_immediately_before_request(peer, when):
    server, transport, value = peer
    count = 0
    def guard():
        nonlocal count
        count += 1
        if count == when: raise ValueError("handoff_lease_lost")
    with pytest.raises(ValueError, match="handoff_lease_lost"):
        transport.submit(value, HandoffWindow(), guard=guard)
    assert not server.calls


@pytest.mark.parametrize("kind", ["trickle", "trickle_headers"])
def test_one_deadline_bounds_headers_and_entire_response(peer, kind):
    server, transport, value = peer
    setattr(server, kind, True)
    start = time.monotonic()
    with pytest.raises(OwnerUnavailable, match="handoff_(exchange_expired|write_uncertain|response_protocol)"):
        transport.submit(value, HandoffWindow(seconds=0.12))
    assert time.monotonic() - start < 1


@pytest.mark.parametrize("endpoint", ["https://127.0.0.1:1", "http://localhost:1", "http://127.0.0.1",
    "http://user@127.0.0.1:1", "http://127.0.0.1:1/path", "http://127.0.0.1:99999"])
def test_endpoint_is_explicit_loopback_without_userinfo_or_path(endpoint):
    with pytest.raises(ValueError, match="handoff_endpoint"):
        OwnerTransport("owner", "research", endpoint, "t"*32)


def test_window_does_not_reset_call_or_byte_ceilings():
    window = HandoffWindow()
    for _ in range(4): window.start()
    with pytest.raises(ValueError, match="handoff_exchange_limit"): window.start()
    with pytest.raises(ValueError, match="handoff_response_total_limit"): window.consume(4194305)
    with pytest.raises(ValueError, match="handoff_deadline"): HandoffWindow(True)
