"""Installed source orchestration, successor transfer and public retained-history replacement."""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("solver_installed_environment", Path(__file__).with_name("environment.py"))
ENV = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ENV)
HTTP = ENV.HTTP


def scenarios(e):
    seed_tool = e.stages["seed"]
    config = {**e.oracle["config"], "source_pins": seed_tool.image["golden_input"]["source_pins"]}
    seed = e.publish(seed_tool, config)
    port = seed_tool.descriptor["inputs"][0]
    command = e.command("graph.admit", {"plan_sha256": e.plans["initial-population"]["sha256"], "budget": {"limit": 100},
        "inputs": [{"port": "parameters", "value": {"kind": "artifact", "artifact": seed, "representation": port["representation"], "unit": port["unit"]}}]})
    admitted = HTTP.decoded(e.runtime.endpoint, "/v1/graph-runs", e.tokens["admin"], command)
    assert admitted["outcome"]["status"] == "accepted", admitted
    parent = e.active_run = admitted["outcome"]["committed"]["object_id"]
    first, reports = e.execute()
    assert first["spent"] == 5
    cut, state = e.export(parent, reports[-1])
    original_bytes = e.bytes(state)
    e.replace_runtime()
    assert e.graph() == first and e.bytes(state) == original_bytes
    assert HTTP.decoded(e.runtime.endpoint, "/v1/graph-runs", e.tokens["admin"], command) == admitted
    assert e.export(parent, reports[-1])[0] == cut
    e.record("SOLVER-INITIAL-REPLACEMENT", {"admission": admitted, "graph": first, "source_cut": cut, "retained_state": state})

    source = cut["sources"][0]
    successor_command = e.command("graph.admit_successor", {"plan_sha256": e.plans["continued-generations"]["sha256"],
        "budget": {"limit": 100}, "inputs": [], "predecessor": cut["predecessor"],
        "carried": [{"target_port": "parameters", "source": source["source"], "expected_value_sha256": source["value_sha256"]}]})
    successor = HTTP.decoded(e.runtime.endpoint, "/v1/graph-runs/successors", e.tokens["admin"], successor_command)
    assert successor["outcome"]["status"] == "accepted", successor
    child = e.active_run = successor["outcome"]["committed"]["object_id"]
    page, following = e.execute()
    assert page["spent"] == 12 and len(following) == 12
    reports += following
    assert [item["result"]["generation"] for item in reports if item["stage"] == "retain"] == [0, 1, 2]
    for expected in e.oracle["generations"]:
        scores = [item["input"]["candidate"] for item in reports if item["stage"] == "score" and item["input"]["candidate"]["generation"] == expected["generation"]]
        scores.sort(key=lambda candidate: candidate["proposal_index"])
        assert [item["candidate_id"] for item in scores] == expected["candidate_ids"]
        assert [item["scoring_seed"] for item in scores] == expected["scoring_seeds"]
        if expected["generation"]:
            assert [item["parent_ids"][0] for item in scores] == expected["parent_ids"]
    final_cut, final = e.export(child, reports[-1])
    lineage_path = "/v1/graph-runs/" + child + "/lineage"
    lineage = HTTP.decoded(e.runtime.endpoint, lineage_path, e.tokens["admin"])
    assert lineage["predecessor"] == cut["predecessor"]
    receipts = {event["response"]["outcome"]["binding"]["reservation_id"]: event["response"]
        for event in e.binding_relay.events if event["path"] == "/v1/reservations" and event["status"] == 200}
    proofs = {key: e.proof(receipt["outcome"]["binding"]) for key, receipt in receipts.items()}
    assert len(receipts) > len(reports) and all(proof["proof"]["status"] == "committed" for proof in proofs.values())
    delivery = []
    for _ in range(12):
        delivery.append(e.owner_command("deliver", "--limit", "100", "--time-budget", "10"))
        retained = {key: HTTP.decoded(e.artifact.endpoint, "/v1/reservations/" + key, e.tokens["runtime"]) for key in receipts}
        if all(receipt["outcome"]["status"] == "confirmed" for receipt in retained.values()):
            break
    assert all(receipt["outcome"]["status"] == "confirmed" for receipt in retained.values())
    final_bytes = e.bytes(final)
    e.replace_runtime()
    assert e.graph() == page and e.bytes(final) == final_bytes
    assert HTTP.decoded(e.runtime.endpoint, lineage_path, e.tokens["admin"]) == lineage
    assert HTTP.decoded(e.runtime.endpoint, "/v1/graph-runs", e.tokens["admin"], command) == admitted
    assert HTTP.decoded(e.runtime.endpoint, "/v1/graph-runs/successors", e.tokens["admin"], successor_command) == successor
    assert HTTP.decoded(e.runtime.endpoint, "/v3/graph-runs/" + parent, e.tokens["admin"]) == first
    assert {key: e.proof(receipt["outcome"]["binding"]) for key, receipt in receipts.items()} == proofs
    e.record("SOLVER-SUCCESSOR-REPLACEMENT", {"parent": parent, "child": child, "graph": page, "lineage": lineage,
        "admission": successor, "source_cut": final_cut, "final": final, "final_state": json.loads(final_bytes),
        "reports": reports, "proofs": proofs, "retained": retained, "delivery": delivery, "plans": e.plans,
        "binding_requests": e.binding_relay.events, "notification_target_configured": False})
    e.active_run = None


def main():
    assert importlib.util.find_spec("amphora_campaign_runtime") is None
    assert importlib.util.find_spec("sqlalchemy") is None
    config = json.loads(Path(sys.argv[1]).read_bytes())
    with tempfile.TemporaryDirectory(prefix="amphora-solver-peers-") as directory:
        e = ENV.SolverEnvironment(config, Path(directory))
        try:
            e.setup()
            scenarios(e)
            e.save("passed")
            print("Installed solver/successor/replacement passed; scope " + e.scope["project_id"], flush=True)
        except BaseException:
            e.save("failed")
            raise
        finally:
            e.close()


if __name__ == "__main__":
    main()
