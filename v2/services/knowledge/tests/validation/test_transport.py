import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from amphora_contracts_research import ResearchQuestion
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.validation.peers import DataReader, ResearchReader
from amphora_knowledge.validation.transport import PeerTransport, PeerUnavailable, ReadBudget, strict_json


@pytest.fixture
def server():
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self):
            self.server.requests.append((self.command, self.path, self.headers.get("Authorization"), b""))
            self.reply()

        def do_POST(self):
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            self.server.requests.append((self.command, self.path, self.headers.get("Authorization"), raw))
            self.reply()

        def reply(self):
            status, content_type, raw = self.server.response
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.close_connection = True
            try:
                if self.server.trickle:
                    for byte in raw:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.04)
                else:
                    self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

        def log_message(self, *args):
            pass

    owner = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    owner.daemon_threads = True
    owner.requests, owner.response, owner.trickle = [], (200, "application/json", b"{}"), False
    thread = threading.Thread(target=owner.serve_forever, daemon=True)
    thread.start()
    owner.client = PeerTransport(f"http://127.0.0.1:{owner.server_port}", "k"*32)
    yield owner
    owner.shutdown()
    owner.server_close()
    thread.join(timeout=2)


@pytest.mark.parametrize("endpoint", ["https://127.0.0.1:1", "http://example.org:1", "http://127.0.0.1",
    "http://127.0.0.1:1/path", "http://secret@127.0.0.1:1", "http://127.0.0.1:99999", "http://127.0.0.1:1?x"])
def test_explicit_peer_endpoint_only(endpoint):
    with pytest.raises(ValueError, match="explicit_loopback_peer_required"):
        PeerTransport(endpoint, "k"*32)


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"x":NaN}', b'{"x":Infinity}', b'\xff', b'{'])
def test_strict_json(raw):
    with pytest.raises(PeerUnavailable, match="peer_protocol_error"):
        strict_json(raw)


@pytest.mark.parametrize("status,exception,code", [(401, KnowledgeError, "peer_access_denied"),
    (403, KnowledgeError, "peer_access_denied"), (404, KnowledgeError, "reference_unavailable"),
    (302, PeerUnavailable, "peer_unavailable"), (503, PeerUnavailable, "peer_unavailable")])
def test_http_failure_no_redirect_or_retry(server, status, exception, code):
    server.response = status, "application/json", b'{"secret":"must not enter diagnostics"}'
    with pytest.raises(exception, match="^" + code + "$"):
        server.client.read("/x", ReadBudget())
    assert len(server.requests) == 1


def test_exact_public_routes_and_scoped_research_body(server, peers):
    data, research = DataReader(server.client), ResearchReader(server.client)
    budget = ReadBudget()
    artifact = peers.source_record.reference.raw
    cases = [(artifact, lambda: data.artifact(artifact, budget), "/v1/artifacts/context"),
        (peers.source_record, lambda: data.source(peers.source_record.reference, budget), "/v1/acquisition/sources/source/r1"),
        (peers.trace_record, lambda: data.trace(peers.proposal.grounding.conversion_traces[0], budget), "/v1/acquisition/traces/conversion"),
        (peers.question_record, lambda: research.question(peers.question_record.reference, budget), "/v1/questions/read"),
        (peers.need_record, lambda: research.need(peers.need_record.reference, budget), "/v1/evidence-needs/read")]
    for record, read, path in cases:
        server.response = 200, "application/json", record.model_dump_json().encode()
        assert read() == record
        assert server.requests[-1][1:3] == (path, "Bearer " + "k"*32)
    assert json.loads(server.requests[-1][3]) == peers.need_record.reference.model_dump(mode="json")
    server.response = 200, "text/plain", peers.raw
    assert data.content(artifact, budget) == peers.raw
    assert budget.calls == 6 and budget.consumed > len(peers.raw)


def test_body_and_aggregate_budgets(server):
    server.response = 200, "application/json", b"12345"
    with pytest.raises(KnowledgeError, match="peer_response_limit"):
        server.client.read("/x", ReadBudget(), limit=4)
    with pytest.raises(KnowledgeError, match="peer_total_bytes_limit"):
        server.client.read("/x", ReadBudget(max_bytes=4))
    budget = ReadBudget(max_calls=1)
    server.client.read("/x", budget)
    with pytest.raises(KnowledgeError, match="peer_call_limit"):
        server.client.read("/x", budget)


@pytest.mark.parametrize("media,raw", [("text/plain", b"{}"), ("application/json", b'{"reference":{}}')])
def test_malformed_records_remain_transient_protocol_failures(server, media, raw):
    server.response = 200, media, raw
    with pytest.raises(PeerUnavailable, match="peer_protocol_error"):
        server.client.record("/x", ResearchQuestion, ReadBudget())


def test_whole_review_deadline_interrupts_trickling_body(server):
    server.trickle = True
    server.response = 200, "application/json", b"x"*100
    started = time.monotonic()
    with pytest.raises(PeerUnavailable):
        server.client.read("/x", ReadBudget(seconds=0.15))
    assert time.monotonic() - started < 1.5
