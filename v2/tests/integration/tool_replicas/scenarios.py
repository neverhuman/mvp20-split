"""Actual registry selection, concurrent invocations and receipt-first completion loss."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("replica_processes", Path(__file__).with_name("processes.py"))
processes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(processes)


def run(e, http):
    tool = e.tools[0]
    catalog = http.decoded(e.registry.endpoint, "/v1/releases?capability_id=" + tool.lock["tool"]["capability_id"], e.tokens["admin"])
    assert [item["lock"] for item in catalog["items"]] == [tool.lock]
    selection = e.registry_call("resolve", {"release": catalog["items"][0]["lock"], "context": "synthetic-tests",
        "inputs": tool.descriptor["inputs"], "outputs": tool.descriptor["outputs"]})
    assert selection["decision"]["status"] == "candidate", selection["reason_code"]
    selected = selection["decision"]["observations"]["release"]
    assert selected == tool.lock
    fixture = e.fixtures[tool.module + "-2"]
    assert all(item["tool"] == selected["tool"] for item in fixture["invocations"])
    admitted = http.decoded(e.runtime.endpoint, "/v1/fixture-runs", e.tokens["admin"],
        e.command("runtime.admit_fixture", fixture))
    assert admitted["outcome"]["status"] == "accepted"
    e.active_run = admitted["outcome"]["committed"]["object_id"]
    e.record("REPLICA-REGISTRY-TO-RUNTIME", {"catalog": catalog, "selection": selection, "admission": admitted,
        "heartbeats": tool.heartbeats, "run_id": e.active_run})
    first, second = (processes.Worker(e, http, tool, actor) for actor in ("worker1", "worker2"))
    claims = [worker.wait("claimed") for worker in (first, second)]
    invocations = [claim["outcome"]["invocation"] for claim in claims]
    assert len({item["invocation_id"] for item in invocations}) == 2
    assert len({item["attempt_id"] for item in invocations}) == 2
    state = http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run, e.tokens["admin"])
    assert state["status"] == "running" and all(a["status"] == "leased" for a in state["activations"])
    assert {a["latest_attempt"]["worker_id"] for a in state["activations"]} == {"worker1", "worker2"}
    assert state["budget"] == {"limit": 4, "available": 2, "reserved": 2, "spent": 0}
    e.record("REPLICA-DISTINCT-CONCURRENT-CLAIMS", {"claims": claims, "snapshot": state})
    first.resume()
    second.resume()
    publications = [worker.wait("published") for worker in (first, second)]
    before = http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run, e.tokens["admin"])
    assert before["status"] == "running" and all(a["status"] == "leased" for a in before["activations"])
    assert len({item["artifact"]["artifact_id"] for item in publications}) == 2
    e.runtime_relay.drop_path = "/v1/invocations/complete"
    first.resume()
    second.resume()
    outcomes = [worker.result() for worker in (first, second)]
    assert all(value["status"] == "completion_accepted" and value["outcome"] == "succeeded" for value in outcomes)
    final = http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run, e.tokens["admin"])
    assert final["status"] == "completed" and all(a["status"] == "succeeded" for a in final["activations"])
    assert final["budget"] == {"limit": 4, "available": 2, "reserved": 0, "spent": 2}
    records = []
    for worker, invocation, publication in zip((first, second), invocations, publications, strict=True):
        path = "/v1/commands/runtime.complete/complete-" + invocation["attempt_id"]
        receipt = http.decoded(e.runtime.endpoint, path + "?actor_id=" + worker.actor, e.tokens["admin"])
        report_id = receipt["outcome"]["committed"]["object_id"]
        report = http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run + "/completions/" + report_id, e.tokens["admin"])
        assert report["canonical_result"] is True and len(report["retention_reservation_ids"]) == 1
        reference = report["result"]["outcome"]["outputs"][0]["artifact"]
        assert reference == publication["artifact"]
        actual = http.decoded(e.artifact.endpoint, "/v1/artifacts/" + reference["artifact_id"] + "/content", e.tokens[worker.actor])
        assert actual == tool.image["golden_output"]
        records.append({"receipt": receipt, "completion": report, "result": actual})
    dropped = [event for event in e.runtime_relay.events if event.get("fault") == "response_dropped_after_owner_success"]
    assert len(dropped) == 1
    identity = dropped[0]["identity"]
    assert sum(event.get("identity") == identity for event in e.runtime_relay.events) == 1
    path = "/v1/commands/runtime.complete/" + identity["command_id"]
    assert any(event["method"] == "GET" and event["path"] == path for event in e.runtime_relay.events)
    e.record("REPLICA-PUBLICATION-AND-LOST-COMPLETION", {"before_completion": before, "snapshot": final, "records": records,
        "runtime_requests": list(e.runtime_relay.events), "artifact_requests": list(e.artifact_relay.events)})
    e.active_run = None
