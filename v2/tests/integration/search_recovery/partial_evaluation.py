"""Actual one-accepted/one-interrupted evaluation, retained history and fenced retry."""

import os
import subprocess
import time
from datetime import UTC, datetime


def receipt(e, http, identity):
    return http.decoded(e.runtime.endpoint, "/v1/commands/" + identity["command_family"] + "/" + identity["command_id"] +
                        "?actor_id=" + identity["actor_id"], e.tokens["admin"])


def completed(e, http, identity):
    accepted = receipt(e, http, identity)
    assert accepted["outcome"]["status"] == "accepted"
    return http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run + "/completions/" + accepted["outcome"]["committed"]["object_id"], e.tokens["admin"])


class PartialEvaluationInterruption:
    stage = "evaluate"

    def __init__(self):
        self.verified = False
        self.evidence = {}

    def interrupt(self, e, http, worker_command):
        command, env = worker_command(e, "evaluate", "worker1", http)
        first = subprocess.run(command, cwd=e.root, env=env, capture_output=True, timeout=90)
        assert first.returncode == 0
        import json
        assert json.loads(first.stdout)["status"] == "completion_accepted"
        self.saved_identity = next(event["identity"] for event in reversed(e.runtime_relay.events)
            if event.get("identity", {}).get("command_family") == "runtime.complete")
        self.saved_completion = completed(e, http, self.saved_identity)
        self.saved_bytes = e.bytes(self.saved_completion["result"]["outcome"]["outputs"][0]["artifact"])
        first_event, first_claim = len(e.artifact_relay.events), len(e.runtime_relay.events)
        command, env = worker_command(e, "evaluate", "worker2", http, lease_seconds=10)
        e.artifact_relay.hold_finalize = True
        e.artifact_relay.reached.clear()
        e.artifact_relay.release.clear()
        process = subprocess.Popen(command, cwd=e.root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            assert e.artifact_relay.reached.wait(20) and process.poll() is None
            finalized = next(event for event in e.artifact_relay.events[first_event:] if event.get("barrier") == "actual_finalization_before_runtime_response")
            self.orphan = finalized["response"]["artifact"]
            self.orphan_bytes = e.bytes(self.orphan)
            identities = [event["identity"] for event in e.runtime_relay.events[first_claim:]
                          if event.get("identity", {}).get("command_family") == "runtime.claim"]
            assert len(identities) == 1 and identities[0]["actor_id"] == "worker2"
            self.invocation = receipt(e, http, identities[0])["outcome"]["invocation"]
            assert completed(e, http, self.saved_identity) == self.saved_completion
        finally:
            if process.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=True, capture_output=True,
                                   timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    process.kill()
            process.communicate(timeout=10)
            e.artifact_relay.release.set()
        view = http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run, e.tokens["admin"])
        active = next(item for item in view["activations"] if item["invocation_id"] == self.invocation["invocation_id"])
        expiry = datetime.fromisoformat(active["latest_attempt"]["lease_expires_at"])
        delay = max(0, (expiry - datetime.now(UTC)).total_seconds()) + 0.1
        assert delay <= 12
        original_view = e.restart_runtime(e.config["replacement_runtime"])
        e.config["runtime"] = e.config["replacement_runtime"]
        if delay:
            time.sleep(delay)
        assert completed(e, http, self.saved_identity) == self.saved_completion
        self.claim_offset = len(e.runtime_relay.events)
        self.evidence = {"accepted_before_interruption": self.saved_completion, "interrupted_invocation": self.invocation,
                         "finalized_unaccepted_artifact": self.orphan, "runtime_restart_view": original_view, "lease_wait_seconds": delay}

    def verify_retry(self, e, http):
        identities = [event["identity"] for event in e.runtime_relay.events[self.claim_offset:]
                      if event.get("identity", {}).get("command_family") == "runtime.claim"]
        matches = []
        for identity in identities:
            claim = receipt(e, http, identity)
            invocation = claim["outcome"].get("invocation")
            if invocation and invocation["invocation_id"] == self.invocation["invocation_id"]:
                matches.append((identity["actor_id"], invocation))
        assert len(matches) == 1
        actor, retry = matches[0]
        assert retry["attempt_id"] != self.invocation["attempt_id"] and retry["fence"] == self.invocation["fence"] + 1
        accepted = completed(e, http, {"actor_id": actor, "command_family": "runtime.complete", "command_id": "complete-" + retry["attempt_id"]})
        assert e.bytes(accepted["result"]["outcome"]["outputs"][0]["artifact"]) == self.orphan_bytes
        saved = completed(e, http, self.saved_identity)
        assert saved == self.saved_completion and e.bytes(saved["result"]["outcome"]["outputs"][0]["artifact"]) == self.saved_bytes
        before = http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run, e.tokens["admin"])
        late = e.command("runtime.complete", {"run_id": e.active_run, "completion": {"schema_version": "1",
            "invocation_id": self.invocation["invocation_id"], "attempt_id": self.invocation["attempt_id"], "fence": self.invocation["fence"],
            "outcome": {"status": "succeeded", "outputs": [{"port": "result", "artifact": self.orphan}]}}}, "worker2")
        rejected = http.decoded(e.runtime.endpoint, "/v1/invocations/complete", e.tokens["worker2"], late)
        assert rejected["outcome"]["reason_code"] == "stale_attempt"
        assert http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run, e.tokens["admin"]) == before
        self.evidence.update(retried_completion=accepted, stale_completion=rejected, original_accepted_history_unchanged=True)
        self.verified = True
