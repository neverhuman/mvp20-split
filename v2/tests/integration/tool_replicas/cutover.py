"""A new immutable release is selected only between campaigns; prior pins/history remain."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("replica_cutover_operations", Path(__file__).with_name("operations.py"))
operations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operations)


def run(e, http):
    old = next(tool for tool in e.tools if tool.previous)
    new = next(tool for tool in e.tools if tool.pending_replacement)
    assert old.lock["tool"]["release"] == "0.2.0" and new.lock["tool"]["release"] == "0.3.0"
    assert old.lock["tool"]["image_sha256"] != new.lock["tool"]["image_sha256"]
    assert old.lock["input_schemas"] == new.lock["input_schemas"] and old.lock["output_schemas"] == new.lock["output_schemas"]
    assert old.descriptor["outputs"][0]["representation"] == "symbol-sequence"
    assert new.descriptor["outputs"][0]["representation"] == "symbol-statistics"
    unavailable = e.registry_call("resolve", {"release": new.lock, "context": "synthetic-tests",
        "inputs": new.descriptor["inputs"], "outputs": new.descriptor["outputs"]})
    assert unavailable["reason_code"] == "release_not_active"
    old_selection = operations.select(e, old)
    earlier = operations.Campaign(e, http, old)
    old_record = earlier.finish(earlier.worker("worker1"))
    old_snapshot = earlier.snapshot()
    assert e.active_run is None
    e.activate(new)
    drained = e.registry_call("drain", {"release": old.lock, "expected_revision": 2})
    assert drained["release"]["status"] == "draining" and drained["release"]["lock"] == old.lock
    rejected_old = e.registry_call("resolve", {"release": old.lock, "context": "synthetic-tests",
        "inputs": old.descriptor["inputs"], "outputs": old.descriptor["outputs"]})
    assert rejected_old["reason_code"] == "release_not_active"
    new_selection = operations.select(e, new)
    later = operations.Campaign(e, http, new)
    wrong = operations.processes.Worker(e, http, old, "worker1")
    observed = wrong.wait("claimed")
    assert observed["outcome"]["status"] == "no_eligible_work"
    wrong.resume()
    assert wrong.result() == {"status": "no_eligible_work"}
    assert later.snapshot()["activations"][0]["latest_attempt"] is None
    new_record = later.finish(later.worker("worker2"))
    assert earlier.snapshot() == old_snapshot
    prior_attempt = old_record["completion"]["result"]["attempt_id"]
    assert earlier.report(prior_attempt, "worker1") == old_record
    historical = http.decoded(e.registry.endpoint, "/v1/releases/" + old.lock["descriptor_sha256"], e.tokens["admin"])
    assert historical["lock"] == old.lock and historical["descriptor"] == old.image["descriptor"]
    assert e.registry_call("register", {"scope": e.scope, "descriptor": old.image["descriptor"], "expected_lock": old.lock})["release"]["lock"] == old.lock
    e.record("REPLICA-IMMUTABLE-RELEASE-CUTOVER", {"old_selection": old_selection, "new_selection": new_selection,
        "old_pin_after_drain": historical, "wrong_release_claim": observed, "old_record": old_record,
        "new_record": new_record, "old_snapshot_preserved": old_snapshot, "new_snapshot": later.snapshot()})
