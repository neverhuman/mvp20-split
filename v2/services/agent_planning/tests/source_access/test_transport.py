"""Real loopback scripted HTTP, distinct from actual Data-owner acceptance."""

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from amphora_agent_planning.source_access import DataReader, ReadBudget, SourceUnavailable
from amphora_contracts_core import Scope


@pytest.fixture
def peer():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.server.calls.append((self.path, self.headers.get("Authorization")))
            if self.server.delay_headers:
                time.sleep(0.4)
            try:
                if self.server.trickle_headers:
                    self.connection.sendall(b"HTTP/1.1 200 OK\r\nX-Slow: ")
                    for _ in range(30):
                        self.connection.sendall(b"x")
                        time.sleep(0.03)
                    return
                self.send_response(self.server.status)
                self.send_header("Content-Type", self.server.media)
                self.send_header("Content-Length", str(len(self.server.body)))
                self.end_headers()
                if self.server.trickle:
                    for byte in self.server.body:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.03)
                else:
                    self.wfile.write(self.server.body)
            except OSError:
                pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    server.calls, server.status, server.media = [], 200, "application/json"
    server.body = b'{"tenant_id":"t","project_id":"p"}'
    server.trickle = server.delay_headers = server.trickle_headers = False
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    reader = DataReader(f"http://127.0.0.1:{server.server_port}", "t" * 32)
    yield server, reader
    server.shutdown()
    server.server_close()
    thread.join(2)


def test_explicit_authenticated_bounded_record_and_empty_payload(peer):
    server, reader = peer
    budget = ReadBudget()
    record = reader.record("/v1/artifacts/a", Scope, budget)
    assert record == Scope(tenant_id="t", project_id="p")
    assert server.calls == [("/v1/artifacts/a", "Bearer " + "t" * 32)]
    assert budget.calls == 1 and budget.consumed == len(server.body)
    server.body = b""
    assert reader.read("/v1/artifacts/a/processing-content", budget, limit=0, json_body=False) == b""


@pytest.mark.parametrize("status,error,code", [(401, ValueError, "source_access_denied"),
    (403, ValueError, "source_access_denied"), (404, ValueError, "source_reference_unavailable"),
    (302, SourceUnavailable, "source_peer_unavailable"), (503, SourceUnavailable, "source_peer_unavailable")])
def test_status_classification_is_redacted_and_never_retries_or_redirects(peer, status, error, code):
    server, reader = peer
    server.status, server.body = status, b"secret peer diagnostic"
    with pytest.raises(error, match="^" + code + "$"):
        reader.read("/v1/artifacts/a", ReadBudget())
    assert len(server.calls) == 1


@pytest.mark.parametrize("body", [b'{"x":1,"x":2}', b'{"x":NaN}', b"\xff", b"{}", b"[]", b"{"])
def test_malformed_metadata_is_transient_not_fabricated_authority(peer, body):
    server, reader = peer
    server.body = body
    with pytest.raises(SourceUnavailable, match="source_peer_protocol"):
        reader.record("/v1/artifacts/a", Scope, ReadBudget())


def test_wrong_media_per_response_and_total_bounds(peer):
    server, reader = peer
    server.media = "text/plain"
    with pytest.raises(SourceUnavailable, match="source_peer_protocol"):
        reader.record("/v1/artifacts/a", Scope, ReadBudget())
    server.media = "application/json"
    with pytest.raises(ValueError, match="source_peer_response_limit"):
        reader.read("/v1/artifacts/a", ReadBudget(), limit=3)
    with pytest.raises(ValueError, match="source_review_byte_limit"):
        reader.read("/v1/artifacts/a", ReadBudget(max_bytes=3))
    budget = ReadBudget(max_calls=1)
    reader.read("/v1/artifacts/a", budget)
    before = len(server.calls)
    with pytest.raises(ValueError, match="source_review_call_limit"):
        reader.read("/v1/artifacts/a", budget)
    assert len(server.calls) == before


@pytest.mark.parametrize("phase", ["headers", "body", "trickle_headers"])
def test_whole_review_deadline_interrupts_stall_or_trickle(peer, phase):
    server, reader = peer
    server.delay_headers = phase == "headers"
    server.trickle = phase == "body"
    server.trickle_headers = phase == "trickle_headers"
    server.body = b"x" * 100
    start = time.monotonic()
    with pytest.raises(SourceUnavailable):
        reader.read("/v1/artifacts/a", ReadBudget(seconds=0.12))
    assert time.monotonic() - start < 1.5
    assert len(server.calls) == 1


def test_connection_failure_is_redacted_without_retry():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    reader = DataReader(f"http://127.0.0.1:{port}", "t" * 32)
    budget = ReadBudget(seconds=1)
    with pytest.raises(SourceUnavailable, match="^source_peer_unavailable$"):
        reader.read("/v1/artifacts/a", budget)
    assert budget.calls == 1


@pytest.mark.parametrize("endpoint", [None, "", "https://127.0.0.1:80", "http://example.com:80",
    "http://localhost:80", "http://127.0.0.1", "http://127.0.0.1:bad", "http://127.0.0.1:0",
    "http://u:p@127.0.0.1:80", "http://127.0.0.1:80/path", "http://127.0.0.1:80?x=1"])
def test_endpoint_is_explicit_local_owner_not_model_controlled(endpoint):
    with pytest.raises(ValueError, match="source_peer_endpoint"):
        DataReader(endpoint, "t" * 32)


@pytest.mark.parametrize("token", [None, "short", "x" * 513, "x" * 31 + "\n"])
def test_invalid_credentials_fail_before_network(token):
    with pytest.raises(ValueError, match="source_peer_credential"):
        DataReader("http://127.0.0.1:80", token)


@pytest.mark.parametrize("kwargs", [{"seconds": True}, {"seconds": float("inf")}, {"seconds": 0},
                                    {"max_calls": 513}, {"max_bytes": 33554433}])
def test_invalid_review_limits_are_not_unbounded(kwargs):
    with pytest.raises(ValueError):
        ReadBudget(**kwargs)


def test_invalid_paths_limits_and_expired_review_do_not_contact_peer(peer):
    server, reader = peer
    for path in ("/v1/artifacts/a/content", "/v1/artifacts/a?use=read", "/v1/artifacts/../a", "https://elsewhere"):
        with pytest.raises(ValueError, match="source_peer_path"):
            reader.read(path, ReadBudget())
    with pytest.raises(ValueError, match="source_peer_response_limit"):
        reader.read("/v1/artifacts/a", ReadBudget(), limit=4194305)
    budget = ReadBudget()
    budget.deadline = time.monotonic() - 1
    with pytest.raises(SourceUnavailable, match="source_review_deadline"):
        reader.read("/v1/artifacts/a", budget)
    assert not server.calls


def test_reader_methods_use_only_explicit_public_routes(peer):
    from pathlib import Path

    from amphora_contracts_core import ArtifactRef
    from amphora_contracts_evidence import ConversionTraceRef, SourceRevisionRef

    server, reader = peer
    fixture = json.loads((Path(__file__).parents[1] / "extraction/fixtures/extraction.json").read_bytes())
    artifact = ArtifactRef.model_validate_json(json.dumps(fixture["request"]["context"]["objective"]))
    server.body = artifact.model_dump_json().encode()
    assert reader.artifact(artifact, ReadBudget()) == artifact
    server.body = b"x" * artifact.size_bytes
    assert reader.content(artifact, ReadBudget()) == server.body
    source = SourceRevisionRef.model_validate_json(json.dumps(fixture["task"]["sources"][0]["source"]))
    trace = ConversionTraceRef.model_validate_json(json.dumps(fixture["task"]["sources"][0]["conversion_traces"][0]))
    server.body = b"{}"
    for operation in (lambda: reader.source(source, ReadBudget()), lambda: reader.trace(trace, ReadBudget())):
        with pytest.raises(SourceUnavailable, match="source_peer_protocol"):
            operation()
    assert [path for path, _ in server.calls] == [f"/v1/artifacts/{artifact.artifact_id}",
        f"/v1/artifacts/{artifact.artifact_id}/processing-content",
        f"/v1/acquisition/sources/{source.source_id}/{source.revision_id}", f"/v1/acquisition/traces/{trace.trace_id}"]
