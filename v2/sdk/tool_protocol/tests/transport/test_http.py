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
    "http://127.0.0.1/extra", "http://127.0.0.1?secret=yes", "file:///tmp/example",
    "http://127.0.0.1:bad", "http://127.0.0.1:99999", "http://[invalid", None])
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


@pytest.mark.parametrize("token", ["short", "a" * 31 + "\0", "a" * 31 + "\x7f", "a" * 31 + "é"])
def test_credentials_must_be_bounded_printable_ascii(token):
    with pytest.raises(ProtocolError, match="invalid_service_credential"):
        HttpTransport("http://127.0.0.1", token)


@pytest.mark.parametrize("timeout", [0, -1, 31, True, float("nan"), "5", None])
def test_invalid_timeouts(timeout):
    with pytest.raises(ProtocolError, match="invalid_transport_timeout"):
        HttpTransport("http://127.0.0.1", "a" * 32, timeout=timeout)


def test_invalid_request_path_and_limit_are_local_errors():
    transport = HttpTransport("http://127.0.0.1", "a" * 32)
    for path in ("https://other/", "/v1/x?redirect=yes", "/v1/x\nInjected:yes"):
        with pytest.raises(ProtocolError, match="invalid_service_path"):
            transport.request("GET", path)
    for limit in (-1, 16777217, True):
        with pytest.raises(ProtocolError, match="invalid_response_limit"):
            transport.request("GET", "/v1/x", limit=limit)


def test_bounded_query_encodes_cursor_as_data_and_preserves_plain_paths(peer):
    from urllib.parse import parse_qs, urlsplit
    endpoint,calls=peer
    transport=HttpTransport(endpoint,"a"*32)
    cursor="abc+/=&next=secret#x"
    assert transport.request("GET","/v1/data",query={"cursor":cursor,"limit":8,"frontier_only":False}).status==200
    parsed=urlsplit(calls[-1][0])
    assert parsed.path=="/v1/data" and parse_qs(parsed.query)=={"cursor":[cursor],"limit":["8"],"frontier_only":["false"]}
    transport.request("GET","/v1/data")
    assert calls[-1][0]=="/v1/data"


@pytest.mark.parametrize("method,query",[("POST",{"cursor":"a"}),("GET",{}),("GET",{"a":[]}),
    ("GET",{"cursor":"a"*4097}),("GET",{"a&x":"value"}),("GET",{"a":"bad\nvalue"}),
    ("GET",{str(i):"x" for i in range(13)}),("GET",{str(i):"x"*4096 for i in range(5)})])
def test_invalid_queries_reject_locally_without_sending_credentials(peer,method,query):
    endpoint,calls=peer
    with pytest.raises(ProtocolError,match="invalid_service_query"):
        HttpTransport(endpoint,"a"*32).request(method,"/v1/data",query=query)
    assert calls==[]
