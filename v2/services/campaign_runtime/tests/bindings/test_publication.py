"""Public HTTP publication replay; server is a scripted protocol peer."""

import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.artifact_bindings.model import BindingAddress
from amphora_campaign_runtime.artifact_bindings.publication import ArtifactPublisher
from amphora_campaign_runtime.coordinator.projections import ProjectionUnavailable
from amphora_contracts_core import SchemaRef, Scope


@pytest.fixture
def publication_peer():
    state = SimpleNamespace(streams=0, finalized=None, lose=False, commands=[], auth=[])

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def respond(self, status, body):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())

        def do_GET(self):
            state.auth.append(self.headers.get("Authorization"))
            if state.finalized is None:
                self.respond(404, {})
            else:
                self.respond(200, state.finalized)

        def do_PUT(self):
            state.auth.append(self.headers.get("Authorization"))
            state.streams += 1
            state.body = self.rfile.read(int(self.headers["Content-Length"]))
            self.respond(200, {"schema_version": "1", "upload_id": "upload", "attempt_id": "stream", "generation": state.streams, "status": "streamed"})

        def do_POST(self):
            from amphora_contracts_artifacts import parse_command
            state.auth.append(self.headers.get("Authorization"))
            body = self.rfile.read(int(self.headers["Content-Length"]))
            raw = json.loads(body)
            family = raw["identity"]["command_family"]
            command = parse_command(family, body)
            state.commands.append(command)
            content = raw["payload"]["content"]
            if family == "artifacts.begin_upload":
                self.respond(200, {"schema_version": "1", "scope": raw["identity"]["scope"], "content": content, "upload_id": "upload"})
            else:
                assert hashlib.sha256(state.body).hexdigest() == content["sha256"]
                receipt = {"schema_version": "1", "upload_id": "upload", "artifact": {**content,
                    "scope": raw["identity"]["scope"], "artifact_id": "published"}}
                state.finalized = {"schema_version": "1", "identity": raw["identity"], "operation_id": "publication",
                    "request_sha256": command.sha256, "outcome": {"status": "finalized", "receipt": receipt}}
                if state.lose:
                    state.lose = False
                    self.respond(503, {})
                else:
                    self.respond(200, receipt)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield state, "http://127.0.0.1:" + str(server.server_port)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("lost", [False, True])
def test_finalized_receipt_replay_never_streams_again(publication_peer, lost):
    state, endpoint = publication_peer
    state.lose = lost
    peer = ArtifactPublisher(endpoint, "t" * 32, "binding-owner")
    address = BindingAddress(Scope(tenant_id="test", project_id="bindings"), "run", "a" * 64, "b" * 64)
    schema = SchemaRef(schema_id="fixture", version="1", sha256="c" * 64)
    body = b'{"values":[1,2]}'
    if lost:
        with pytest.raises(ProjectionUnavailable):
            peer.publish(address, "result", body, schema, lambda: None)
    first = peer.publish(address, "result", body, schema, lambda: None)
    second = ArtifactPublisher(endpoint, "t" * 32, "binding-owner").publish(address, "result", body, schema, lambda: None)
    assert first == second and state.streams == 1
    assert all(value == "Bearer " + "t" * 32 for value in state.auth)
    begins = [command for command in state.commands if command.identity.command_family == "artifacts.begin_upload"]
    assert len({command.sha256 for command in begins}) == 1
