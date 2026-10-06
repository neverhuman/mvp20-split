"""Kill only the owned vary process after real finalization, then prove fenced replay."""

import os
import subprocess
import time
from datetime import UTC, datetime


class FinalizationInterruption:
    def __init__(self):
        self.verified = False
        self.evidence = {}

    def interrupt(self, e, http, worker_command):
        first = len(e.artifact_relay.events)
        claims = len(e.runtime_relay.events)
        command, env = worker_command(e, "vary", "worker1", http, lease_seconds=10)
        e.artifact_relay.hold_finalize = True
        e.artifact_relay.reached.clear()
        e.artifact_relay.release.clear()
        process = subprocess.Popen(command, cwd=e.root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            assert e.artifact_relay.reached.wait(20), "Actual tool finalization barrier was not reached"
            assert process.poll() is None
            finalized = next(event for event in e.artifact_relay.events[first:]
                             if event.get("barrier") == "actual_finalization_before_runtime_response")
            self.orphan = finalized["response"]["artifact"]
            self.raw = e.bytes(self.orphan)
            identities = [event["identity"] for event in e.runtime_relay.events[claims:]
                          if event.get("identity", {}).get("command_family") == "runtime.claim"]
            assert len(identities) == 1
            claim = http.decoded(e.runtime.endpoint, "/v1/commands/runtime.claim/" + identities[0]["command_id"] +
                                 "?actor_id=worker1", e.tokens["admin"])
            self.invocation = claim["outcome"]["invocation"]
        finally:
            if process.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=True,
                                   capture_output=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    process.kill()
            process.communicate(timeout=10)
            e.artifact_relay.release.set()
        run = http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run, e.tokens["admin"])
        activation = next(item for item in run["activations"] if item["invocation_id"] == self.invocation["invocation_id"])
        expiry = datetime.fromisoformat(activation["latest_attempt"]["lease_expires_at"])
        delay = max(0, (expiry - datetime.now(UTC)).total_seconds()) + 0.1
        assert delay <= 12
        before = e.restart_runtime()
        if delay:
            time.sleep(delay)
        self.evidence = {"killed_attempt": self.invocation, "finalized_unaccepted_artifact": self.orphan,
                         "runtime_restart_snapshot": before, "expiry_wait_seconds": delay}

    def verify_retry(self, e, http):
        run = http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run, e.tokens["admin"])
        identity = next(event["identity"] for event in reversed(e.runtime_relay.events)
                        if event.get("identity", {}).get("command_family") == "runtime.claim")
        claimed = http.decoded(e.runtime.endpoint, "/v1/commands/runtime.claim/" + identity["command_id"] +
                               "?actor_id=worker1", e.tokens["admin"])
        retry = claimed["outcome"]["invocation"]
        assert retry["invocation_id"] == self.invocation["invocation_id"]
        assert retry["attempt_id"] != self.invocation["attempt_id"]
        assert retry["fence"] == self.invocation["fence"] + 1
        attempt = retry["attempt_id"]
        receipt = http.decoded(e.runtime.endpoint, "/v1/commands/runtime.complete/complete-" + attempt +
                              "?actor_id=worker1", e.tokens["admin"])
        completion = http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run + "/completions/" +
                                 receipt["outcome"]["committed"]["object_id"], e.tokens["admin"])
        accepted = completion["result"]["outcome"]["outputs"][0]["artifact"]
        assert e.bytes(accepted) == self.raw
        late = e.command("runtime.complete", {"run_id": e.active_run, "completion": {"schema_version": "1",
            "invocation_id": self.invocation["invocation_id"], "attempt_id": self.invocation["attempt_id"],
            "fence": self.invocation["fence"], "outcome": {"status": "succeeded", "outputs": [{"port": "result", "artifact": self.orphan}]}}}, "worker1")
        rejected = http.decoded(e.runtime.endpoint, "/v1/invocations/complete", e.tokens["worker1"], late)
        assert rejected["outcome"]["status"] == "rejected" and rejected["outcome"]["reason_code"] == "stale_attempt", rejected
        assert http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run, e.tokens["admin"]) == run
        self.evidence.update(replacement_claim=claimed, accepted_artifact=accepted, late_receipt=rejected,
                             canonical_varied_bytes_equal=True)
        self.verified = True
