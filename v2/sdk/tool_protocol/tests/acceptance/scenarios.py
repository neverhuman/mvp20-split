"""Independent oracles for actual worker/owner success, ambiguity and expiry."""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


def run(e, http):
    worker_env = dict(http.isolated_env(), WORKER_RUNTIME_TOKEN=e.tokens["worker"], WORKER_ARTIFACT_TOKEN=e.tokens["worker"])
    assert not any("DATABASE" in name or "MIGRATION" in name or name == "PYTHONPATH" for name in worker_env)

    def start(tool, variant="golden"):
        definition = e.fixtures[tool.module + "-" + variant]
        admitted = http.decoded(e.runtime.endpoint, "/v1/fixture-runs", e.tokens["admin"],
                               e.command("runtime.admit_fixture", definition))
        e.active_run = admitted["outcome"]["committed"]["object_id"]
        e.artifact_relay.events.clear()
        e.runtime_relay.events.clear()
        return e.active_run

    def worker_config(tool, *, wrong_pin=False):
        config = {"actor_id": "worker", "scope": e.scope, "run_id": e.active_run,
            "image_sha256": "f" * 64 if wrong_pin else tool.descriptor["binding"]["image_sha256"],
            "runtime": {"endpoint": e.runtime_relay.endpoint, "token_env": "WORKER_RUNTIME_TOKEN"},
            "artifacts": {"endpoint": e.artifact_relay.endpoint, "token_env": "WORKER_ARTIFACT_TOKEN"},
            "lease_seconds": 10}
        path = e.root / "worker.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    def worker(tool, **kwargs):
        result = subprocess.run([tool.python, "-I", "-m", tool.module, "worker", "--config", str(worker_config(tool, **kwargs))],
            cwd=e.root, env=worker_env, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, "Independent tool worker failed: " + result.stderr[-200:]
        return json.loads(result.stdout)

    def snapshot():
        return http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run, e.tokens["admin"])

    def report():
        state = snapshot()
        attempt = state["activations"][0]["latest_attempt"]
        receipt = http.decoded(e.runtime.endpoint, "/v1/commands/runtime.complete/complete-" + attempt["attempt_id"]
            + "?actor_id=worker", e.tokens["admin"])
        report_id = receipt["outcome"]["committed"]["object_id"]
        value = http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run + "/completions/" + report_id, e.tokens["admin"])
        return state, receipt, value

    def success(tool, outcome):
        assert outcome["status"] == "completion_accepted" and outcome["outcome"] == "succeeded", outcome
        state, receipt, value = report()
        assert state["status"] == "completed" and value["canonical_result"] is True
        reference = value["result"]["outcome"]["outputs"][0]["artifact"]
        actual = http.decoded(e.artifact.endpoint, "/v1/artifacts/" + reference["artifact_id"] + "/content", e.tokens["worker"])
        assert actual == tool.image["golden_output"]
        assert value["result"]["fence"] == state["activations"][0]["fence"]
        assert len(value["retention_reservation_ids"]) == 1
        return {"run_id": e.active_run, "receipt": receipt, "completion": value, "result": actual}

    def record(name, facts):
        e.cases.append({"case": name, "observed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **facts,
            "runtime_requests": list(e.runtime_relay.events), "artifact_requests": list(e.artifact_relay.events)})
        e.save_evidence("running")
        print(name + " passed", flush=True)

    def cancel_running():
        if snapshot()["status"] == "running":
            receipt = http.decoded(e.runtime.endpoint, "/v1/runs/cancel", e.tokens["admin"],
                e.command("runtime.cancel", {"run_id": e.active_run, "reason_code": "test_cleanup"}))
            assert receipt["outcome"]["status"] == "accepted"

    for tool in e.tools:
        start(tool)
        record("WORKER-GOLDEN-" + tool.module, success(tool, worker(tool)))
    numeric, sequence = e.tools
    for name, relay, path in (("WORKER-LOST-UPLOAD", e.artifact_relay, "/v1/uploads"),
        ("WORKER-LOST-FINALIZE", e.artifact_relay, "/v1/artifacts/finalize"),
        ("WORKER-LOST-COMPLETE", e.runtime_relay, "/v1/invocations/complete")):
        start(numeric)
        relay.drop_path = path
        facts = success(numeric, worker(numeric))
        dropped = [event for event in relay.events if event.get("fault") == "response_dropped_after_owner_success"]
        assert len(dropped) == 1
        identity = dropped[0]["identity"]
        assert sum(event.get("identity") == identity for event in relay.events) == 1
        lookup = "/v1/commands/" + identity["command_family"] + "/" + identity["command_id"]
        assert any(event["method"] == "GET" and event["path"] == lookup for event in relay.events)
        record(name, facts)

    start(sequence, "invalid-symbol")
    assert worker(sequence)["outcome"] == "failed"
    state, receipt, value = report()
    assert state["status"] == "failed"
    assert value["result"]["outcome"] == {"status": "failed", "reason_code": "invalid_sequence_symbol", "retryable": False}
    assert not any(event["method"] == "POST" for event in e.artifact_relay.events)
    record("WORKER-INVALID-SYMBOL", {"run_id": e.active_run, "receipt": receipt, "completion": value})

    start(numeric)
    e.artifact_relay.interrupt_stream = True
    assert worker(numeric)["outcome"] == "failed"
    _state, receipt, value = report()
    assert value["result"]["outcome"]["retryable"] is True
    assert any(event.get("fault") == "partial_body_disconnect" for event in e.artifact_relay.events)
    assert not any(event["path"] == "/v1/artifacts/finalize" for event in e.artifact_relay.events)
    record("WORKER-INTERRUPTED-STREAM", {"run_id": e.active_run, "receipt": receipt, "completion": value})
    cancel_running()

    start(numeric)
    assert worker(numeric, wrong_pin=True) == {"status": "no_eligible_work"}
    assert snapshot()["activations"][0]["latest_attempt"] is None
    assert not e.artifact_relay.events
    definition = e.fixtures[numeric.module + "-golden"]
    # Worker credentials have no admission privilege even against a valid prepared definition.
    assert http.request(e.runtime.endpoint, "/v1/fixture-runs", e.tokens["worker"],
        e.command("runtime.admit_fixture", definition, "worker"))[0] == 403
    record("WORKER-EXACT-PIN-AND-NO-ADMISSION", success(numeric, worker(numeric)))

    start(numeric)
    marker = e.root / "compute-barrier.json"
    child = subprocess.Popen([numeric.python, "-I", str(Path(__file__).with_name("worker_probe.py")),
        numeric.module, str(worker_config(numeric)), "expire", str(marker)], cwd=e.root, env=worker_env,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 30
        while not marker.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert marker.exists(), "Actual worker did not reach the computation barrier"
        old = snapshot()["activations"][0]["latest_attempt"]
        time.sleep(11)  # Actual requested DB lease is ten seconds; no clock mutation.
        child.stdin.write("continue\n")
        child.stdin.flush()
        stdout, _stderr = child.communicate(timeout=15)
        assert child.returncode == 3 and json.loads(stdout)["status"] == "authority_or_transport_lost"
        assert not any(event["method"] == "POST" for event in e.artifact_relay.events)
        assert not any(event["path"] == "/v1/invocations/complete" for event in e.runtime_relay.events)
        expired_requests = list(e.runtime_relay.events)
        facts = success(numeric, worker(numeric))
        new = snapshot()["activations"][0]["latest_attempt"]
        assert new["fence"] == old["fence"] + 1 and new["attempt_id"] != old["attempt_id"]
        record("WORKER-EXPIRED-AND-RECLAIMED", {**facts, "expired_attempt": old, "expired_worker_requests": expired_requests})
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate(timeout=10)
    e.active_run = None
