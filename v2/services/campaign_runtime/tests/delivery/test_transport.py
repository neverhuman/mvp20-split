"""HTTP notification replay deduplicates consumer effects; no exactly-once network claim."""

import json
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.completion.artifacts import ArtifactReservations
from amphora_campaign_runtime.delivery.store import DeliveryStore
from amphora_campaign_runtime.delivery.transport import DeliveryTargets, DeliveryUnavailable, NotificationSink
from amphora_campaign_runtime.delivery.worker import DeliveryWorker
from sqlalchemy import text


@pytest.fixture
def sink():
    state = SimpleNamespace(mode="ack", requests=[], effects=set(), receipt=None)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass
        def do_POST(self):
            assert self.headers.get("Authorization") == "Bearer " + "x" * 32
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state.requests.append(body)
            if state.receipt is not None:
                ack = state.receipt
            else:
                state.effects.add(body["operation_id"])
                ack = {k: body[k] for k in ("scope", "operation_id", "event_id")}
                ack["status"] = "acknowledged"
                if state.mode == "wrong":
                    ack["operation_id"] = "wrong"
            raw = json.dumps(ack).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    state.endpoint = f"http://127.0.0.1:{server.server_port}/notifications"
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_send_before_ack_loss_replays_same_operation_without_second_effect(delivery_env, sink):
    d = delivery_env
    store = DeliveryStore(d.env.engine)
    first, other = store.claim(d.principal)
    store.finish(d.principal, other, acknowledged=True)
    target = NotificationSink(sink.endpoint, "x" * 32)
    target.send(first)  # Consumer commits, delivery worker disappears before acknowledging.
    with d.env.engine.begin() as conn:
        conn.execute(text(f"UPDATE runtime.{first.journal} SET lease_expires_at=clock_timestamp()-interval '1 second' "
                          "WHERE operation_id=:operation"), {"operation": first.operation_id})
    replacement = store.claim(d.principal)[0]
    target.send(replacement)
    assert sink.requests[0] == sink.requests[1]
    assert len(sink.effects) == 1
    assert store.finish(d.principal, first, acknowledged=True) is False
    assert store.finish(d.principal, replacement, acknowledged=True)


def test_wrong_ack_is_not_success_and_sweep_has_explicit_bounds(delivery_env, sink):
    d = delivery_env
    store = DeliveryStore(d.env.engine)
    target = NotificationSink(sink.endpoint, "x" * 32)
    targets = DeliveryTargets(notifications={"runtime_notifications": target, "runtime_policy_notifications": target})
    sink.mode = "wrong"
    result = DeliveryWorker(store, targets).sweep(d.principal, limit=1)
    assert result == {"claimed": 1, "acknowledged": 0, "failed": 1, "stale": 0}
    sink.mode = "ack"
    result = DeliveryWorker(store, targets).sweep(d.principal, limit=1)
    assert result["acknowledged"] == 1
    assert len(sink.effects) == 2


def test_missing_target_keeps_delivery_for_retry(delivery_env):
    d = delivery_env
    claim = DeliveryStore(d.env.engine).claim(d.principal, limit=1)[0]
    with pytest.raises(DeliveryUnavailable, match="target_unavailable"):
        DeliveryTargets().send(claim)


def test_artifact_terminal_delivery_validates_exact_receipt(delivery_env, sink):
    d = delivery_env
    base = DeliveryStore(d.env.engine).claim(d.principal, limit=1)[0]
    artifact = d.env.raw["payload"]["invocations"][0]["inputs"][0]["artifact"]
    binding = {"reservation_id": "reservation", "artifact": artifact, "intent": {
        "runtime_owner": "runtime", "intent_id": "intent", "semantic_completion_sha256": "a" * 64,
        "output_binding": "output"}}
    identity = {"actor_id": "runtime", "command_id": "delivery", "scope": d.principal.scope.model_dump(),
                "command_family": "artifacts.confirm"}
    command = {"identity": identity, "payload": {"reservation_id": "reservation", "intent_id": "intent", "runtime_receipt_id": "commit"}}
    claim = replace(base, target="artifact_confirm", payload={"command": command, "binding": binding})
    targets = DeliveryTargets(ArtifactReservations("runtime", sink.endpoint, "x" * 32))
    sink.receipt = {"outcome": {"status": "confirmed", "binding": binding,
                                "proof": {"status": "committed", "runtime_receipt_id": "commit"}}}
    targets.send(claim)
    sink.receipt["outcome"]["proof"]["runtime_receipt_id"] = "wrong"
    with pytest.raises(DeliveryUnavailable, match="ack_mismatch"):
        targets.send(claim)
    command = {"identity": {**identity, "command_family": "artifacts.reconcile"},
               "payload": {"reservation_id": "reservation"}}
    claim = replace(base, target="artifact_reconcile", payload={"command": command, "binding": binding})
    sink.receipt = {"outcome": {"status": "released", "binding": binding,
        "proof": {"status": "aborted", "runtime_receipt_id": "cancel", "reason_code": "cancelled"}}}
    targets.send(claim)
    sink.receipt["outcome"]["binding"] = {**binding, "reservation_id": "wrong"}
    with pytest.raises(DeliveryUnavailable, match="ack_mismatch"):
        targets.send(claim)
