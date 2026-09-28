"""Live unchanged-pin, checkpoint denial, duplicate result and finite-budget oracles."""

import copy
import importlib.util
import json
import time
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location("replica_negative_operations", Path(__file__).with_name("operations.py"))
operations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operations)
spec = importlib.util.spec_from_file_location("replica_negative_wire", Path(__file__).with_name("wire.py"))
wire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wire)


def run(e, http):
    tool = next(tool for tool in e.tools if tool.pending_replacement)
    campaign = operations.Campaign(e, http, tool)
    worker = campaign.worker("worker1")
    invocation = worker.wait("claimed")["outcome"]["invocation"]
    before = campaign.snapshot()
    release_path = "/v1/releases/" + tool.lock["descriptor_sha256"]
    release = http.decoded(e.registry.endpoint, release_path, e.tokens["admin"])
    invalid = copy.deepcopy(tool.image["descriptor"])
    invalid["tool"]["purpose"] = "An incompatible replacement attempting to overwrite a registered identity."
    changed_lock = wire.release_lock(invalid)
    rejected = e.registry_call("register", {"scope": e.scope, "descriptor": invalid, "expected_lock": changed_lock})
    assert rejected["status"] == "rejected" and rejected["reason_code"] == "immutable_release_conflict"
    assert http.decoded(e.registry.endpoint, release_path, e.tokens["admin"]) == release
    assert http.request(e.registry.endpoint, "/v1/releases/" + changed_lock["descriptor_sha256"], e.tokens["admin"])[0] == 404
    assert campaign.snapshot() == before and invocation["tool"] == tool.lock["tool"]
    worker.resume()
    publication = worker.wait("published")
    output = publication["artifact"]
    payload = {"run_id": campaign.run_id, "completion": {"schema_version": "1", "invocation_id": invocation["invocation_id"],
        "attempt_id": invocation["attempt_id"], "fence": invocation["fence"],
        "outcome": {"status": "succeeded", "outputs": [{"port": "result", "artifact": output}], "checkpoint": None}}}
    published = campaign.snapshot()
    rejected_checkpoints = []
    for version in ("1", "2"):
        proposal = copy.deepcopy(payload)
        checkpoint = copy.deepcopy(output)
        checkpoint["schema_ref"]["version"] = version
        proposal["completion"]["outcome"]["checkpoint"] = checkpoint
        command = e.command("runtime.complete", proposal, "worker1")
        status, body = http.request(e.runtime.endpoint, "/v1/invocations/complete", e.tokens["worker1"], command)
        receipt = json.loads(body)
        if version == "1":
            assert status == 200 and receipt["outcome"]["status"] == "rejected"
            assert receipt["outcome"]["reason_code"] == "checkpoint_binding_mismatch"
        else:
            assert status == 422 and receipt == {"reason_code": "invalid_command"}
            assert http.request(e.runtime.endpoint, "/v1/commands/runtime.complete/" + command["identity"]["command_id"]
                + "?actor_id=worker1", e.tokens["admin"])[0] == 404
        assert campaign.snapshot() == published
        rejected_checkpoints.append({"schema_version": version, "http_status": status, "response": receipt})
    revision = http.decoded(e.runtime.endpoint, "/v1/invocations/complete", e.tokens["worker1"],
        e.command("runtime.complete", {**payload, "expected_checkpoint_revision": 99}, "worker1"))
    assert revision["outcome"]["reason_code"] == "checkpoint_revision_conflict"
    assert campaign.snapshot() == published
    worker.resume()
    assert worker.result()["outcome"] == "succeeded"
    original = campaign.report(invocation["attempt_id"], "worker1")
    final = campaign.snapshot()
    assert final["status"] == "completed" and final["budget"] == {"limit": 2, "available": 1, "reserved": 0, "spent": 1}
    exact = e.command("runtime.complete", payload, "worker1", "complete-" + invocation["attempt_id"])
    replay = http.decoded(e.runtime.endpoint, "/v1/invocations/complete", e.tokens["worker1"], exact)
    assert replay == original["receipt"]
    duplicate = http.decoded(e.runtime.endpoint, "/v1/invocations/complete", e.tokens["worker1"],
        e.command("runtime.complete", payload, "worker1"))
    assert duplicate["outcome"]["status"] == "rejected" and duplicate["outcome"]["reason_code"] == "run_not_running"
    audit = http.decoded(e.runtime.endpoint, "/v1/runs/" + campaign.run_id + "/audit?kind=completion_accepted", e.tokens["admin"])
    assert len(audit["entries"]) == 1 and audit["next_cursor"] is None
    assert campaign.snapshot() == final and campaign.report(invocation["attempt_id"], "worker1") == original
    e.record("REPLICA-FAILED-REPLACEMENT-CHECKPOINT-DUPLICATE", {"run_id": campaign.run_id,
        "registration_rejection": rejected, "preserved_release": release, "claimed_invocation": invocation,
        "checkpoint_rejections": rejected_checkpoints, "checkpoint_revision_rejection": revision, "original": original,
        "replayed_receipt": replay, "duplicate_rejection": duplicate, "snapshot": final, "accepted_audit": audit})
    e.active_run = None

    numeric = e.tools[0]
    limited = operations.Campaign(e, http, numeric, "budget-one")
    dead = limited.worker("worker1", lease_seconds=10)
    first = dead.wait("claimed")
    dead.close()
    time.sleep(11)
    no_work = []
    for actor in ("worker1", "worker2"):
        contender = limited.worker(actor)
        observed = contender.wait("claimed")
        assert observed["outcome"]["status"] == "no_eligible_work"
        contender.resume()
        assert contender.result() == {"status": "no_eligible_work"}
        state = limited.snapshot()
        assert state["budget"] == {"limit": 1, "available": 0, "reserved": 0, "spent": 1}
        assert state["activations"][0]["attempt_count"] == 1
        no_work.append(observed)
    before_cancel = limited.snapshot()
    # Fixture-only Runtime has no graph supervisor loop; the controller tears down its own run.
    cancelled = http.decoded(e.runtime.endpoint, "/v1/runs/cancel", e.tokens["admin"],
        e.command("runtime.cancel", {"run_id": limited.run_id, "reason_code": "replica_acceptance_cleanup"}))
    assert cancelled["outcome"]["status"] == "accepted"
    e.active_run = None
    e.record("REPLICA-FINITE-BUDGET", {"run_id": limited.run_id, "first_claim": first,
        "subsequent_claims": no_work, "snapshot_before_cleanup": before_cancel, "cleanup_receipt": cancelled})

    replacement = e.config.get("replacements", {}).get(tool.module)
    assert replacement and Path(replacement).parent != Path(tool.python).parent, "Fresh README-boundary installation required"
    fresh = SimpleNamespace(**{**vars(tool), "python": replacement})
    rebuilt = operations.Campaign(e, http, fresh)
    record = rebuilt.finish(rebuilt.worker("worker2"))
    assert campaign.snapshot() == final and campaign.report(invocation["attempt_id"], "worker1") == original
    e.record("REPLICA-FRESH-REPLACEMENT-CONFORMANCE", {"fresh_install": True, "lock": tool.lock,
        "preserved_run_id": campaign.run_id, **record})
