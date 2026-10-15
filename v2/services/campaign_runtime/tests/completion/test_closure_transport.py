"""Scripted public closure peer; actual Data acceptance is qualified separately."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
from amphora_contracts_artifacts import ReserveArtifact
from amphora_campaign_runtime.completion.artifacts import ReservationUnavailable
from amphora_campaign_runtime.completion.closures import ClosureReservations, PROFILE


@pytest.fixture
def closure_peer():
    state = SimpleNamespace(mode="valid", calls=[])
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            state.calls.append((self.path, None, self.headers.get("Authorization")))
            if self.path == "/ready":
                code, body = (503, {"ready": False}) if state.mode == "not_ready" else (200, {"ready": True})
            elif state.mode == "old_owner":
                code, body = 404, {"detail": "Not Found"}
            elif state.mode == "denied":
                code, body = 403, {"reason_code": "access_denied"}
            else:
                code, body = 404, {"reason_code": "reservation_unavailable"}
            raw = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            command = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state.calls.append((self.path, command, self.headers.get("Authorization")))
            payload = dict(command["payload"])
            payload.pop("profile")
            root = {"outcome": {"status": "reserved", "binding": {"reservation_id": "r1", **payload}}}
            body = {"profile": PROFILE, "reservation": root, "artifact_count": 3, "members_sha256": "d" * 64}
            if state.mode == "ordinary":
                body = root
            elif state.mode == "mismatch":
                root["outcome"]["binding"]["artifact"]["sha256"] = "f" * 64
            elif state.mode == "unknown_profile":
                body["profile"] = "future"
            elif state.mode == "over_limit":
                body["artifact_count"] = 4097
            elif state.mode == "bool_count":
                body["artifact_count"] = True
            raw = json.dumps(body).encode() if state.mode != "oversized" else b" " * 262145
            self.send_response(302 if state.mode == "redirect" else 200)
            if state.mode == "redirect":
                self.send_header("Location", "/other")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    state.endpoint = f"http://127.0.0.1:{server.server_port}/v1/retention-closures/reserve"
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def reservation():
    return ReserveArtifact.model_validate({"artifact": {"artifact_id": "root",
        "scope": {"tenant_id": "tenant", "project_id": "project"}, "sha256": "a" * 64,
        "size_bytes": 20, "media_type": "application/json",
        "schema_ref": {"schema_id": "test", "version": "1", "sha256": "b" * 64}},
        "intent": {"runtime_owner": "runtime", "intent_id": "intent", "output_binding": "output",
                   "semantic_completion_sha256": "c" * 64}})


def test_closure_transport_preserves_membership_and_stable_command(closure_peer):
    client = ClosureReservations("runtime", closure_peer.endpoint, "x" * 32)
    first = client.reserve(reservation())
    assert first.artifact_count == 3 and first.members_sha256 == "d" * 64
    assert client.reserve(reservation()) == first
    assert closure_peer.calls[0] == closure_peer.calls[1]
    path, command, authorization = closure_peer.calls[0]
    assert path == "/v1/retention-closures/reserve"
    assert authorization == "Bearer " + "x" * 32
    assert command["identity"]["command_family"] == "artifacts.reserve_derived_closure"
    assert command["payload"]["profile"] == PROFILE


@pytest.mark.parametrize("mode", ["ordinary", "mismatch", "unknown_profile", "over_limit", "bool_count", "oversized", "redirect"])
def test_closure_transport_rejects_incompatible_receipts(closure_peer, mode):
    closure_peer.mode = mode
    with pytest.raises(ReservationUnavailable):
        ClosureReservations("runtime", closure_peer.endpoint, "x" * 32).reserve(reservation())


def test_closure_transport_rejects_wrong_owner_without_io(closure_peer):
    with pytest.raises(ReservationUnavailable, match="runtime_owner_mismatch"):
        ClosureReservations("other", closure_peer.endpoint, "x" * 32).reserve(reservation())
    assert closure_peer.calls == []


def test_read_only_preflight_checks_route_and_migration_readiness(closure_peer):
    ClosureReservations("runtime", closure_peer.endpoint, "x" * 32).require_available()
    assert closure_peer.calls[0][0] == "/ready"
    assert closure_peer.calls[1][0].startswith("/v1/retention-closures/")
    assert closure_peer.calls[1][2] == "Bearer " + "x" * 32
    assert all(call[1] is None for call in closure_peer.calls)


@pytest.mark.parametrize("mode", ["not_ready", "old_owner", "denied"])
def test_preflight_rejects_unavailable_or_incompatible_owner(closure_peer, mode):
    closure_peer.mode = mode
    with pytest.raises(ReservationUnavailable):
        ClosureReservations("runtime", closure_peer.endpoint, "x" * 32).require_available()
