"""Public artifact transport against a scripted HTTP peer, not real artifact acceptance."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.completion.artifacts import ArtifactReservations, ReservationUnavailable
from amphora_campaign_runtime.completion.model import CompletionProposal, PreparedIntent


@pytest.fixture
def peer():
    state = SimpleNamespace(mode="reserved", calls=[])
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass
        def do_POST(self):
            command = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state.calls.append((command, self.headers.get("Authorization")))
            if state.mode == "redirect":
                self.send_response(302)
                self.send_header("Location", "/other")
                self.end_headers()
                return
            binding = {"reservation_id": "r1", **command["payload"]}
            if state.mode == "mismatch":
                binding["intent"]["semantic_completion_sha256"] = "f" * 64
            raw = json.dumps({"outcome": {"status": "reserved", "binding": binding}}).encode()
            if state.mode == "oversized":
                raw = b" " * 262145
            self.send_response(200)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    state.endpoint = f"http://127.0.0.1:{server.server_port}/reserve"
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_authenticated_transport_has_stable_identity_and_exact_binding(completion_env, peer):
    c = completion_env
    request = PreparedIntent("intent", CompletionProposal.from_command(c.command("runtime.complete", c.payload)), "runtime").reservations()[0]
    client = ArtifactReservations("runtime", peer.endpoint, "x" * 32)
    first = client.reserve(request)
    assert client.reserve(request) == first
    assert peer.calls[0] == peer.calls[1]
    assert peer.calls[0][1] == "Bearer " + "x" * 32
    for mode in ("redirect", "mismatch", "oversized"):
        peer.mode = mode
        with pytest.raises(ReservationUnavailable):
            client.reserve(request)


@pytest.mark.parametrize("endpoint", ["http://example.com/reserve", "https://user:pass@example.com", "http://127.0.0.1/reserve?caller=1"])
def test_unsafe_endpoint_configuration_rejects(endpoint):
    with pytest.raises(ValueError, match="configuration"):
        ArtifactReservations("runtime", endpoint, "x" * 32)
