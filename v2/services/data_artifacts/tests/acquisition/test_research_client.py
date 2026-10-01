import hashlib
import json
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from types import SimpleNamespace

import pytest
from amphora_contracts_core import ArtifactRef, SchemaRef, Scope
from amphora_contracts_evidence import SourceRevisionRef
from amphora_contracts_research import CandidateRevisionRef, ResolveIdentity, SampleRevisionRef
from amphora_data_artifacts.acquisition.adapters import prepare_document, prepare_lab
from amphora_data_artifacts.acquisition.provenance import SourceDocument
from amphora_data_artifacts.acquisition.research import (
    ResearchClient,
    ResearchLookupError,
    lab_identity_query,
)


def query():
    scope = Scope(tenant_id="client", project_id="fixture")
    return ResolveIdentity(wire_version="1", scope=scope,
        candidate=CandidateRevisionRef(scope=scope, candidate_id="c", revision=1),
        sample=SampleRevisionRef(scope=scope, sample_id="s", revision=1))


def response():
    return query().model_dump(mode="json") | {"disposition": "matched", "reason": "exact_identity_only", "authority": "identity_only"}


@pytest.fixture
def peer():
    state = SimpleNamespace(status=200, body=json.dumps(response()).encode(), media="application/json", calls=[], drop=False)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            state.calls.append((self.path, self.headers.get("Authorization"), json.loads(raw)))
            if state.drop:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            self.send_response(state.status)
            self.send_header("Content-Type", state.media)
            self.send_header("Content-Length", str(len(state.body)))
            self.end_headers()
            self.wfile.write(state.body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = Thread(target=server.serve_forever, kwargs={"poll_interval": .01}, daemon=True)
    worker.start()
    try:
        yield state, ResearchClient(f"http://127.0.0.1:{server.server_port}", "a"*32)
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


def test_public_lookup_preserves_original_scoped_identity(peer):
    state, client = peer
    result = client.resolve(query())
    assert result.disposition == "matched" and result.authority == "identity_only"
    assert state.calls == [("/v1/identities/resolve", "Bearer " + "a"*32, query().model_dump(mode="json"))]
    state.body = json.dumps(response() | {"disposition": "quarantined", "reason": "unknown_sample"}).encode()
    assert client.resolve(query()).reason == "unknown_sample"


@pytest.mark.parametrize(("status", "code"), [(401, "research_access_denied"), (403, "research_access_denied"),
    (503, "research_unavailable"), (302, "research_unavailable"), (500, "research_unavailable")])
def test_transport_status_never_invents_unknown_sample(peer, status, code):
    state, client = peer
    state.status = status
    with pytest.raises(ResearchLookupError, match=code):
        client.resolve(query())
    assert len(state.calls) == 1


@pytest.mark.parametrize(("body", "code"), [
    (b'{}', "research_protocol_error"),
    (b'{"wire_version":"1","wire_version":"2"}', "research_protocol_error"),
    (b'{"wire_version":NaN}', "research_protocol_error"),
    (b'\xff', "research_protocol_error"),
    (b' ' * 16385, "research_response_limit"),
], ids=lambda value: f"bytes-{len(value)}" if isinstance(value, bytes) else value)
def test_response_bounds_and_strict_json(peer, body, code):
    state, client = peer
    state.body = body
    with pytest.raises(ResearchLookupError, match=code):
        client.resolve(query())


@pytest.mark.parametrize("mutation", [
    lambda x: x["scope"].update(project_id="wrong"),
    lambda x: x["candidate"].update(revision=2),
    lambda x: x["sample"].update(sample_id="different"),
    lambda x: x.update(reason="unknown_sample"),
    lambda x: x.update(disposition="quarantined"),
])
def test_response_must_match_request_and_its_own_disposition(peer, mutation):
    state, client = peer
    value = response()
    mutation(value)
    state.body = json.dumps(value).encode()
    with pytest.raises(ResearchLookupError, match="research_binding_mismatch"):
        client.resolve(query())


def test_connection_loss_and_wrong_media_are_not_accepted(peer):
    state, client = peer
    state.media = "text/html"
    with pytest.raises(ResearchLookupError, match="research_protocol_error"):
        client.resolve(query())
    state.drop = True
    with pytest.raises(ResearchLookupError, match="research_unavailable"):
        client.resolve(query())


def test_foreign_nested_request_is_rejected_before_network(peer):
    state, client = peer
    request = query()
    request = request.model_copy(update={"sample": request.sample.model_copy(
        update={"scope": request.scope.model_copy(update={"project_id": "foreign"})})})
    with pytest.raises(ResearchLookupError, match="request_scope_mismatch"):
        client.resolve(request)
    assert not state.calls


@pytest.mark.parametrize("endpoint", ["https://127.0.0.1:80", "http://example.invalid:80", "http://127.0.0.1",
    "http://127.0.0.1:80/path", "http://user@127.0.0.1:80", "http://127.0.0.1:80?token=secret"])
def test_endpoint_is_explicit_local_configuration(endpoint):
    with pytest.raises(ValueError):
        ResearchClient(endpoint, "a"*32)


def test_preparation_maps_only_explicit_valid_identities():
    raw = b'{"candidate_id":"c","candidate_revision":"1","sample_id":"s","sample_revision":"1"}'
    scope = query().scope

    def prepare(raw):
        artifact = ArtifactRef(artifact_id="raw", scope=scope, sha256=hashlib.sha256(raw).hexdigest(),
            size_bytes=len(raw), media_type="application/octet-stream",
            schema_ref=SchemaRef(schema_id="fixture", version="1", sha256="a"*64))
        return SourceDocument(SourceRevisionRef(scope=scope, source_id="lab", revision_id="r1", raw=artifact), raw)

    assert lab_identity_query(prepare_lab(prepare(raw))) == query()
    assert lab_identity_query(prepare_lab(prepare(b"{}"))) is None
    assert lab_identity_query(prepare_lab(prepare(raw.replace(b'"sample_revision":"1"', b'"sample_revision":"1.5"')))) is None
    with pytest.raises(ResearchLookupError, match="lab_profile_required"):
        lab_identity_query(prepare_document(prepare(raw)))
