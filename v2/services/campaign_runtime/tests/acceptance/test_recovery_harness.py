"""Fault orchestration accounting must fail closed; hooks stay test-owned."""

import hashlib
import importlib.util
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from amphora_campaign_runtime.hosting import Host

spec = importlib.util.spec_from_file_location("recovery_evidence", Path(__file__).with_name("recovery_evidence.py"))
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)
spec = importlib.util.spec_from_file_location("paired_support", Path(__file__).with_name("paired_support.py"))
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)


def scenario():
    return evidence.ScenarioEvidence("REC-03", {"tenant_id": "t", "project_id": "p"}, {"runtime": "fixture-revision"}, 30)


def test_missing_restart_or_timeout_cannot_claim_recovery(tmp_path):
    record = scenario()
    record.identify(command="complete-1", intent="intent-1", reservation="reservation-1")
    record.event("barrier", "actual reservation response withheld")
    record.event("kill", "owned runtime process")
    record.event("observation", "reserved")
    with pytest.raises(ValueError, match="Incomplete"):
        record.finish()
    record.event("restart", "retained state")
    record.event("failure", "deadline exceeded")
    with pytest.raises(ValueError, match="failed"):
        record.finish()
    path = tmp_path / "failed.json"
    record.save(path)
    assert json.loads(path.read_text())["manifest"]["status"] == "incomplete"


def test_manifest_hash_covers_identities_barriers_and_observations(tmp_path):
    record = scenario()
    record.identify(command="complete-1", run="run-1", attempt="attempt-1")
    with pytest.raises(ValueError):
        record.identify(token="secret")
    for kind in ("barrier", "kill", "restart", "observation"):
        record.event(kind, "owned fixture evidence")
    record.finish()
    path = tmp_path / "passed.json"
    record.save(path)
    envelope = json.loads(path.read_text())
    raw = json.dumps(envelope["manifest"], sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(raw).hexdigest() == envelope["sha256"]
    assert envelope["manifest"]["status"] == "passed"


def test_scenario_deadline_blocks_late_success():
    record = scenario()
    record.identify(command="late-command")
    for kind in ("barrier", "kill", "restart", "observation"):
        record.event(kind, "fixture")
    record.started -= 31
    with pytest.raises(ValueError, match="failed"):
        record.finish()
    assert record.record["status"] == "incomplete"


def test_ordinary_runtime_configuration_rejects_fault_switch(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps({"database_url_env": "UNUSED", "principals": [], "fixtures": [], "fault": "commit"}))
    with pytest.raises(ValueError, match="Explicit"):
        Host.load(path)


@pytest.mark.parametrize("path", ["/v1/invocations/claim", "/v1/invocations/complete", "/v1/reservations/confirm"])
def test_response_barrier_preserves_actual_command_and_reply(path):
    class Owner(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            payload = self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Owner)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    proxy = support.ReservationProxy(f"http://127.0.0.1:{server.server_port}", path)
    proxy.hold_next = True
    command = {"identity": {"command_id": "specific-command"}, "payload": {"value": 3}}
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(support.decoded, proxy.endpoint, path, "fixture-token", command)
            try:
                assert proxy.arrived.wait(timeout=3)
                assert proxy.requests == [command] and proxy.receipts == [command]
                assert not pending.done()
            finally:
                proxy.release.set()
            assert pending.result(timeout=3) == command
    finally:
        proxy.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
