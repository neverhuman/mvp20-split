"""Actual process death, database-clock lease expiry, fenced reclaim and stale report."""

import importlib.util
import time
from pathlib import Path

spec = importlib.util.spec_from_file_location("replica_recovery_operations", Path(__file__).with_name("operations.py"))
operations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operations)


def run(e, http):
    tool = e.tools[0]
    selection = operations.select(e, tool)
    campaign = operations.Campaign(e, http, tool)
    first = campaign.worker("worker1", lease_seconds=10)
    original = first.wait("claimed")["outcome"]["invocation"]
    first.close()
    assert first.child.poll() is not None
    time.sleep(11)  # Actual requested DB lease; no SQL clock or owner state mutation.
    second = campaign.worker("worker2")
    current = second.wait("claimed")["outcome"]["invocation"]
    assert original["invocation_id"] == current["invocation_id"]
    assert current["attempt_id"] != original["attempt_id"] and current["fence"] == original["fence"] + 1
    during = campaign.snapshot()
    assert during["budget"] == {"limit": 2, "available": 0, "reserved": 1, "spent": 1}
    delayed = e.command("runtime.complete", {"run_id": campaign.run_id, "completion": {
        "schema_version": "1", "invocation_id": original["invocation_id"], "attempt_id": original["attempt_id"],
        "fence": original["fence"], "outcome": {"status": "failed", "reason_code": "delayed_worker_report", "retryable": False}}},
        "worker1", "delayed-" + original["attempt_id"])
    rejected = http.decoded(e.runtime.endpoint, "/v1/invocations/complete", e.tokens["worker1"], delayed)
    assert rejected["outcome"]["status"] == "rejected" and rejected["outcome"]["reason_code"] == "stale_attempt"
    assert campaign.snapshot() == during
    record = campaign.finish(second)
    final = campaign.snapshot()
    assert final["budget"] == {"limit": 2, "available": 0, "reserved": 0, "spent": 2}
    assert final["activations"][0]["attempt_count"] == 2
    assert http.decoded(e.runtime.endpoint, "/v1/invocations/complete", e.tokens["worker1"], delayed) == rejected
    assert campaign.snapshot() == final
    e.record("REPLICA-DEATH-RECLAIM-STALE-REPORT", {"selection": selection, "original_invocation": original,
        "reclaimed_invocation": current, "during_reclaim": during, "stale_receipt": rejected, "snapshot": final, **record})
