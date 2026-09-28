"""HTTP-only worker, delivery and independent-branch interruption oracles."""

import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime


def after_expiry(value):
    delay = (datetime.fromisoformat(value) - datetime.now(UTC)).total_seconds()
    assert delay < 5, "Fixture lease exceeded configured bound"
    time.sleep(max(0, delay) + 0.05)  # Wait for the actual owner timestamp, not an assumed lease duration.


def completion(lab, run, invocation, actor="worker"):
    value = {k: invocation[k] for k in ("invocation_id", "attempt_id", "fence")}
    value.update(schema_version="1", outcome={"status": "succeeded", "outputs": [
        {"port": "value", "artifact": lab.output_ref}], "checkpoint": lab.output_ref})
    return lab.command("runtime.complete", {"run_id": run, "completion": value, "expected_checkpoint_revision": 0}, actor)


def report(lab, run, receipt):
    assert receipt["outcome"]["status"] == "accepted", receipt
    report_id = receipt["outcome"]["committed"]["object_id"]
    result = lab.rt(f"/v1/runs/{run}/completions/{report_id}")
    assert result["canonical_result"] is True
    return result


def confirmed(lab, result):
    for reservation in result["retention_reservation_ids"]:
        assert lab.art("/v1/reservations/" + reservation, actor="runtime")["outcome"]["status"] == "confirmed"


def worker(lab, recording):
    with recording(lab, "REC-06") as record:
        admitted = lab.rt("/v1/fixture-runs", lab.command("runtime.admit_fixture", lab.definition))
        run = admitted["outcome"]["committed"]["object_id"]
        claim = lab.command("runtime.claim", {"run_id": run, "worker_id": "worker",
            "tool": lab.definition["invocations"][0]["tool"], "lease_seconds": 2}, "worker")
        child = subprocess.Popen([sys.executable, "-I", str(lab.http_worker)], env=lab.support.isolated_env(),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            child.stdin.write(json.dumps({"endpoint": lab.runtime.endpoint, "token": lab.tokens["worker"],
                "path": "/v1/invocations/claim", "command": claim, "stay": True}) + "\n")
            child.stdin.flush()
            with ThreadPoolExecutor(max_workers=1) as pool:
                reply = json.loads(pool.submit(child.stdout.readline).result(timeout=10))
            assert reply["status"] == 200 and reply["body"]["outcome"]["status"] == "claimed"
            old = reply["body"]["outcome"]
            record.identify(run=run, command=claim["identity"]["command_id"], attempt=old["invocation"]["attempt_id"])
            record.event("barrier", {"claimed_attempt": old["invocation"]["attempt_id"], "expires": old["lease_expires_at"]})
            assert child.poll() is None
            record.event("kill", {"owner": "HTTP-only worker", "pid": child.pid})
            child.kill()
            child.communicate(timeout=10)
            record.event("kill", {"owner": "runtime", "pid": lab.runtime.child.pid})
            lab.runtime.kill()
            lab.runtime.start()
            lab.runtime.ready(lab.tokens["admin"])
            record.event("restart", "runtime retained state; new HTTP-only worker identity")
            after_expiry(old["lease_expires_at"])
            successor = lab.worker("/v1/invocations/claim", lab.command("runtime.claim", {"run_id": run,
                "worker_id": "worker2", "tool": lab.definition["invocations"][0]["tool"], "lease_seconds": 60}, "worker2"))["outcome"]["invocation"]
            assert successor["fence"] == old["invocation"]["fence"] + 1
            assert successor["attempt_id"] != old["invocation"]["attempt_id"]
            record.identify(attempt=successor["attempt_id"])
            assert lab.worker("/v1/invocations/claim", claim) == reply["body"]
            stale = lab.worker("/v1/invocations/complete", completion(lab, run, old["invocation"]))
            assert stale["outcome"]["status"] == "rejected" and stale["outcome"]["reason_code"] == "stale_attempt"
            command = completion(lab, run, successor, "worker2")
            receipt = lab.worker("/v1/invocations/complete", command)
            result = report(lab, run, receipt)
            record.identify(command=command["identity"]["command_id"], intent=result["completion_id"], artifact=lab.output_ref["artifact_id"])
            assert lab.worker("/v1/invocations/complete", command) == receipt
            lab.deliver()
            confirmed(lab, result)
            snapshot = lab.rt("/v1/runs/" + run)
            assert snapshot["status"] == "completed" and snapshot["budget"] == {"limit": 5, "available": 3, "reserved": 0, "spent": 2}
            record.event("observation", "higher successor fence; old claim receipt stable but stale completion rejected; exactly two attempts spent")
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=10)
            if lab.runtime.child.poll() is None:
                lab.rt("/v1/runs/cancel", lab.command("runtime.cancel", {"run_id": run, "reason_code": "cleanup"}))


def delivery(lab, recording):
    with recording(lab, "REC-07") as record:
        run, command = lab.start()
        receipt = lab.worker("/v1/invocations/complete", command)
        result = report(lab, run, receipt)
        record.identify(run=run, command=command["identity"]["command_id"], intent=result["completion_id"],
                        attempt=command["payload"]["completion"]["attempt_id"], artifact=lab.output_ref["artifact_id"])
        lab.proxy.hold_path = "/v1/reservations/confirm"
        lab.proxy.arrived.clear()
        lab.proxy.release.clear()
        lab.proxy.hold_next = True
        offset = len(lab.proxy.receipts)
        child = lab.delivery_process()
        try:
            assert lab.proxy.arrived.wait(timeout=10)
            original = lab.proxy.receipts[offset]
            sent = lab.proxy.requests[offset]
            operation = sent["identity"]["command_id"]
            reservation = sent["payload"]["reservation_id"]
            record.identify(operation=operation, reservation=reservation)
            assert original["outcome"]["status"] == "confirmed"
            held = lab.rt("/v1/deliveries/" + operation)["entries"][0]
            assert held["status"] == "leased"
            assert lab.art("/v1/reservations/" + reservation, actor="runtime") == original
            record.event("barrier", "actual artifact confirm applied; delivery acknowledgement withheld")
            record.event("kill", {"owner": "delivery worker", "pid": child.pid})
            child.kill()
            child.communicate(timeout=10)
            lab.proxy.release.set()
            record.event("kill", {"owner": "runtime", "pid": lab.runtime.child.pid})
            lab.runtime.kill()
            lab.runtime.start()
            lab.runtime.ready(lab.tokens["admin"])
            record.event("restart", "retained delivery lease; replacement delivery process after actual expiry")
            after_expiry(held["lease_expires_at"])
            lab.deliver()
            current = lab.rt("/v1/deliveries/" + operation)["entries"][0]
            assert current["status"] == "acknowledged" and current["generation"] > held["generation"]
            assert current["attempts"] == held["attempts"] + 1
            assert lab.proxy.requests.count(sent) == 2
            assert lab.art("/v1/reservations/" + reservation, actor="runtime") == original
            confirmed(lab, result)
            assert lab.rt("/v1/runs/" + run)["budget"]["spent"] == 1
            record.event("observation", "same operation replayed; exact original terminal peer receipt; successor delivery generation acknowledged; execution unchanged")
        finally:
            lab.proxy.release.set()
            lab.proxy.hold_path = "/v1/reservations"
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=10)


def branches(lab, recording, dropped):
    with recording(lab, "REC-08") as record:
        run, first = lab.start(lab.branches)
        second = lab.worker("/v1/invocations/claim", lab.command("runtime.claim", {"run_id": run, "worker_id": "worker2",
            "tool": lab.definition["invocations"][0]["tool"], "lease_seconds": 60}, "worker2"))["outcome"]["invocation"]
        second_command = completion(lab, run, second, "worker2")
        record.identify(run=run, command=first["identity"]["command_id"], attempt=first["payload"]["completion"]["attempt_id"])
        record.identify(command=second_command["identity"]["command_id"], attempt=second["attempt_id"])
        lab.proxy.arrived.clear()
        lab.proxy.release.clear()
        lab.proxy.hold_next = True
        offset = len(lab.proxy.receipts)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(lab.worker, "/v1/invocations/complete", first)
            try:
                assert lab.proxy.arrived.wait(timeout=10)
                binding = lab.proxy.receipts[offset]["outcome"]["binding"]
                record.identify(intent=binding["intent"]["intent_id"], reservation=binding["reservation_id"], artifact=lab.output_ref["artifact_id"])
                second_receipt = lab.worker("/v1/invocations/complete", second_command)
                second_result = report(lab, run, second_receipt)
                snapshot = lab.rt("/v1/runs/" + run)
                assert snapshot["status"] == "running" and snapshot["budget"]["spent"] == 1 and snapshot["budget"]["reserved"] == 1
                assert sorted(a["status"] for a in snapshot["activations"]) == ["leased", "succeeded"]
                record.event("barrier", "one branch PREPARED/paused; independent branch durably succeeded")
                record.event("kill", {"owner": "runtime", "pid": lab.runtime.child.pid})
                lab.runtime.kill()
            finally:
                lab.proxy.release.set()
            dropped(pending)
        lab.runtime.start()
        lab.runtime.ready(lab.tokens["admin"])
        record.event("restart", "same two-activation state; original independent receipt and frontier recovered")
        assert lab.worker("/v1/invocations/complete", second_command) == second_receipt
        assert lab.rt("/v1/runs/" + run) == snapshot
        first_receipt = lab.worker("/v1/invocations/complete", first)
        first_result = report(lab, run, first_receipt)
        assert first_result["accepted_run_revision"] > second_result["accepted_run_revision"]
        lab.deliver()
        confirmed(lab, first_result)
        confirmed(lab, second_result)
        final = lab.rt("/v1/runs/" + run)
        assert final["status"] == "completed" and final["budget"] == {"limit": 5, "available": 3, "reserved": 0, "spent": 2}
        record.event("observation", "both branches accepted serially across restart; unrelated run revision did not reject valid completion; two spent units")


def exercise(lab, recording, dropped):
    worker(lab, recording)
    delivery(lab, recording)
    branches(lab, recording, dropped)
