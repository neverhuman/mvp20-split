"""Actual loopback transport boundaries; no production owner is substituted here."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from amphora_tool_protocol import HttpTransport, ProtocolError, TransportLost


@pytest.fixture
def peer():
    calls = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            calls.append((self.path, self.headers.get("Authorization")))
            if self.path == "/v1/redirect":
                self.send_response(302)
                self.send_header("Location", "/v1/unrequested")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Length", "50" if self.path == "/v1/truncated" else "4")
            self.end_headers()
            self.wfile.write(b"data")
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(3)


def test_redirect_and_response_bounds(peer, monkeypatch):
    endpoint, calls = peer
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    transport = HttpTransport(endpoint, "a" * 32)
    assert transport.request("GET", "/v1/redirect").status == 302
    assert calls == [("/v1/redirect", "Bearer " + "a" * 32)]
    assert transport.request("GET", "/v1/data", limit=4).body == b"data"
    with pytest.raises(ProtocolError, match="response_limit_exceeded"):
        transport.request("GET", "/v1/data", limit=3)
    # Exact artifact length/hash is also checked by the typed client.
    result = transport.request("GET", "/v1/truncated", limit=100)
    assert result.body == b"data"


@pytest.mark.parametrize("endpoint", ["http://example.com", "http://user:secret@127.0.0.1",
    "http://127.0.0.1/extra", "http://127.0.0.1?secret=yes", "file:///tmp/example"])
def test_invalid_endpoint_never_sends_credentials(endpoint):
    with pytest.raises(ProtocolError, match="invalid_service_endpoint"):
        HttpTransport(endpoint, "a" * 32)


def test_transport_error_is_safe_and_not_automatically_retried(peer, monkeypatch):
    transport = HttpTransport(peer[0], "a" * 32)
    calls = []
    def fail(*_args, **_kwargs):
        calls.append(True)
        raise OSError("sensitive underlying diagnostic")
    monkeypatch.setattr(transport._opener, "open", fail)
    with pytest.raises(TransportLost, match="^transport_lost$"):
        transport.request("GET", "/v1/example")
    assert calls == [True]
