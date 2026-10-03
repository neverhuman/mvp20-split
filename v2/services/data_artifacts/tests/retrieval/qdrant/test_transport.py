"""Socket-level transport policy and explicitly opted-in actual Qdrant readiness."""

import json
import os
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from amphora_data_artifacts.retrieval.qdrant.configuration import VERSION, QdrantConfiguration
from amphora_data_artifacts.retrieval.qdrant.transport import QdrantError, QdrantTransport
from amphora_data_artifacts.retrieval.validation import RetrievalError

TOKEN = "fixture-secret-" + "a" * 40


@contextmanager
def peer(
    raw=b'{"ok":true}',
    *,
    status=200,
    content_type="application/json",
    encoding=None,
    declared=None,
    delay=None,
):
    observed = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            observed.append((self.path, self.headers.get("api-key")))
            try:
                if delay == "headers":
                    for byte in b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n":
                        self.wfile.write(bytes((byte,)))
                        self.wfile.flush()
                        time.sleep(0.05)
                    return
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(raw) if declared is None else declared))
                if encoding:
                    self.send_header("Content-Encoding", encoding)
                self.end_headers()
                if delay == "body":
                    for byte in raw:
                        self.wfile.write(bytes((byte,)))
                        self.wfile.flush()
                        time.sleep(0.05)
                else:
                    self.wfile.write(raw)
            except (OSError, ValueError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_port), observed
    finally:
        server.shutdown()
        server.server_close()
        thread.join(2)


def test_authenticated_request_and_endpoint_independent_backend_identity():
    with peer() as (endpoint, observed):
        config = QdrantConfiguration(endpoint, TOKEN)
        assert TOKEN not in repr(config)
        assert QdrantTransport(config).request("GET", "/") == {"ok": True}
        assert observed == [("/", TOKEN)]
        other = QdrantConfiguration("http://127.0.0.1:23456", "b" * 64, timeout=2)
        assert other.reference == config.reference


@pytest.mark.parametrize(
    "changes",
    [
        {"endpoint": "http://example.com:6333"},
        {"endpoint": "http://user@127.0.0.1:6333"},
        {"endpoint": "http://127.0.0.1:6333/path"},
        {"endpoint": "http://127.0.0.1:6333?secret=x"},
        {"token": "short"},
        {"token": "a" * 40 + "\r\n"},
        {"timeout": True},
        {"timeout": float("nan")},
        {"timeout": 31},
        {"response_limit": True},
        {"response_limit": 1023},
    ],
)
def test_configuration_rejects_unsafe_or_unbounded_values(changes):
    with pytest.raises((RetrievalError, ValueError)):
        QdrantConfiguration(**({"endpoint": "http://127.0.0.1:12345", "token": TOKEN} | changes))


@pytest.mark.parametrize(
    "raw,options,reason",
    [
        (b'{"a":1,"a":2}', {}, "duplicate_key"),
        (b'{"a":NaN}', {}, "nonfinite_json"),
        (b'{"a":1e999}', {}, "nonfinite_json"),
        (b"[]", {}, "response_shape"),
        (b"{", {}, "response_shape"),
        (b"\xff", {}, "response_shape"),
        (b"{}", {"content_type": "text/html"}, "content_type"),
        (b"{}", {"encoding": "gzip"}, "content_encoding"),
        (b"{}", {"declared": 50}, "truncated_response"),
        (b'{"x":"' + b"x" * 1100 + b'"}', {}, "response_bound"),
        (b"{}", {"status": 302}, "http_302"),
        (b"{}", {"status": 401}, "access_denied"),
        (b"{}", {"status": 503}, "http_503"),
    ],
)
def test_malformed_oversized_or_untrusted_response_fails_safely(raw, options, reason):
    with peer(raw, **options) as (endpoint, observed):
        transport = QdrantTransport(QdrantConfiguration(endpoint, TOKEN, response_limit=1024))
        with pytest.raises(QdrantError, match="qdrant_" + reason) as raised:
            transport.request("GET", "/")
        assert TOKEN not in str(raised.value)
        assert len(observed) == 1  # Redirects are never followed.


@pytest.mark.parametrize("delay", ["headers", "body"])
def test_absolute_deadline_covers_trickled_headers_and_body(delay):
    with peer(b'{"text":"a slowly delivered response"}', delay=delay) as (endpoint, _):
        transport = QdrantTransport(QdrantConfiguration(endpoint, TOKEN, timeout=0.2))
        start = time.monotonic()
        with pytest.raises(QdrantError, match="timeout"):
            transport.request("GET", "/")
        assert time.monotonic() - start < 1.0


def test_missing_is_explicit_and_namespace_paths_are_bounded():
    with peer(b"{}", status=404) as (endpoint, observed):
        transport = QdrantTransport(QdrantConfiguration(endpoint, TOKEN))
        path = "/collections/amphora_" + "a" * 64
        assert transport.request("GET", path, allow_missing=True) is None
        with pytest.raises(QdrantError, match="http_404"):
            transport.request("GET", path)
        for method, invalid_path in (
            ("DELETE", path),
            ("GET", "/collections/foreign"),
            ("GET", "http://elsewhere/"),
        ):
            with pytest.raises(RetrievalError):
                transport.request(method, invalid_path)
        assert len(observed) == 2


def test_version_check_never_accepts_unpinned_server():
    with peer(json.dumps({"version": "different"}).encode()) as (endpoint, observed):
        transport = QdrantTransport(QdrantConfiguration(endpoint, TOKEN))
        with pytest.raises(RetrievalError, match="version_mismatch"):
            transport.server()
        assert len(observed) == 1


def test_request_validation_precedes_network_and_closed_peer_is_unavailable():
    with peer(b'{"a":1.25}') as (endpoint, observed):
        transport = QdrantTransport(QdrantConfiguration(endpoint, TOKEN))
        assert transport.request("GET", "/")["a"] == 1.25
        with pytest.raises(QdrantError, match="request_shape"):
            transport.request("POST", "/", {"value": float("nan")})
        assert len(observed) == 1
    with pytest.raises(QdrantError, match="unavailable"):
        transport.request("GET", "/")


def test_deep_json_is_rejected_without_exposing_peer_content():
    with peer(b'{"a":' + b"[" * 1600 + b"0" + b"]" * 1600 + b"}") as (endpoint, _):
        transport = QdrantTransport(QdrantConfiguration(endpoint, TOKEN))
        with pytest.raises(QdrantError, match="json_depth|response_shape"):
            transport.request("GET", "/")


def test_json_depth_and_node_capacity_have_explicit_boundaries():
    from amphora_data_artifacts.retrieval.qdrant.transport import bounded_json

    value = 0
    for _ in range(64):
        value = [value]
    bounded_json(value)
    with pytest.raises(QdrantError, match="json_depth"):
        bounded_json([value])
    bounded_json([None] * 1_999_999)
    with pytest.raises(QdrantError, match="json_node_bound"):
        bounded_json([None] * 2_000_000)


def test_actual_pinned_qdrant_version_and_protected_route_authentication():
    if os.environ.get("AMPHORA_TEST_QDRANT") != "1":
        pytest.skip("Explicit actual Qdrant fixture opt-in required")
    from qdrant_fixture import owned_state

    state = owned_state()
    transport = QdrantTransport(QdrantConfiguration(state["endpoint"], state["api_key"]))
    assert transport.server()["version"] == VERSION
    bad = QdrantTransport(QdrantConfiguration(state["endpoint"], "bad-key-" + "x" * 40))
    with pytest.raises(QdrantError, match="access_denied"):
        bad.server()
