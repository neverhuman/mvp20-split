"""Actual public-owner topology proposal, compilation, carry and retained evidence."""

import importlib.util
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


common = load("common", Path(__file__).with_name("common.py"))
environment = load("topology_environment", Path(__file__).with_name("environment.py"))


def run_graph(e, run, owner):
    e.active_run = run
    worker_result = None
    for _ in range(12):
        receipt = e.call("runtime", "/v1/graph-runs/advance", e.command("graph.advance", {"run_id": run}))
        assert receipt["outcome"]["status"] == "accepted"
        view = e.call("runtime", "/v3/graph-runs/" + run)
        if view["status"] != "running":
            break
        if any(node["kind"] == "invoke" and node["status"] == "issued" for node in view["nodes"]):
            assert worker_result is None, "one known invocation only"
            config = {"actor_id": "worker", "scope": e.scope, "run_id": run, "image_sha256": e.images[owner],
                "runtime": {"endpoint": e.runtime.endpoint, "token_env": "WORKER_TOKEN"},
                "artifacts": {"endpoint": e.artifact.endpoint, "token_env": "WORKER_TOKEN"}, "lease_seconds": 90}
            path = e.root / (owner + "-worker.json")
            path.write_bytes(common.encoded(config))
            result = subprocess.run([e.config[owner], "-I", "-m", "amphora_numeric_affine", "worker", "--config", str(path)],
                cwd=e.root, env=dict(common.HTTP.isolated_env(), WORKER_TOKEN=e.tokens["worker"]), capture_output=True, timeout=90)
            (e.root / (owner + "-worker.log")).write_bytes(result.stdout + result.stderr)
            assert result.returncode == 0
            worker_result = json.loads(result.stdout)
            assert worker_result["status"] == "completion_accepted" and worker_result["outcome"] == "succeeded"
    assert view["status"] == "completed" and view["spent"] == 1 and view["reserved"] == 0
    e.active_run = None
    cut = e.call("runtime", "/v1/graph-runs/" + run + "/carry-sources")
    assert cut["predecessor_ready"]
    completion = e.call("runtime", "/v1/runs/" + run + "/completions/" + worker_result["operation_id"])
    assert completion["canonical_result"]
    producer = e.call("runtime", "/v1/runs/" + run + "/completions/" + worker_result["operation_id"] + "/producer")
    assert producer["completion"] == completion
    assert producer["invocation"]["tool"] == e.locks[owner]["tool"]
    retained = {}
    for _ in range(12):
        result = subprocess.run([e.config["runtime"], "-I", "-m", "amphora_campaign_runtime", "deliver", "--config", e.runtime.config,
                                 "--actor", "admin", "--tenant", e.scope["tenant_id"], "--project", e.scope["project_id"],
                                 "--limit", "100", "--time-budget", "10"], env=e.runtime.env, cwd=e.root, capture_output=True, timeout=30)
        assert result.returncode == 0
        retained = {key: e.call("artifact", "/v1/reservations/" + key, actor="runtime") for key in completion["retention_reservation_ids"]}
        if retained and all(receipt["outcome"]["status"] == "confirmed" for receipt in retained.values()):
            break
    assert retained and all(receipt["outcome"]["status"] == "confirmed" for receipt in retained.values())
    return {"run": run, "view": view, "cut": cut, "worker": worker_result, "completion": completion, "producer": producer, "retained": retained}


def compile_proposal(e, proposal, name):
    from amphora_contracts_commands import NUMERIC_ENCODING
    command = e.command("definition.save", {"draft_id": name, "expected_revision": 0,
        "title": "Synthetic topology successor", "definition": proposal["definition"]})
    command["encoding"] = NUMERIC_ENCODING
    saved = e.call("runtime", "/v1/definition-drafts/save", command)
    assert saved["outcome"]["status"] == "accepted"
    revision = e.call("runtime", "/v1/definition-drafts/" + name)
    validation_command = e.command("definition.validate", {"draft_id": name, "revision": revision["head"]["revision"],
        "content_sha256": revision["head"]["content_sha256"]})
    validated = e.call("runtime", "/v1/definition-drafts/validate", validation_command)
    validation = e.call("runtime", "/v1/definition-validations/" + validated["outcome"]["committed"]["object_id"])
    assert validation["structurally_valid"] and validation["plan_sha256"] != e.plan["sha256"]
    draft = {key: validation[key] for key in ("draft_id", "revision", "content_sha256", "validation_id", "universe_sha256")}
    return {"saved": saved, "save_command": command, "validation_command": validation_command, "validation_receipt": validated,
            "validation": validation, "draft": draft}


def scenario(e):
    value = {"kind": "artifact", "artifact": e.parameters, "representation": e.parameter_type["representation"], "unit": e.parameter_type["unit"]}
    initial_command = e.command("graph.admit", {"plan_sha256": e.plan["sha256"], "inputs": [{"port": "parameters", "value": value}], "budget": {"limit": 16}})
    initial = e.call("runtime", "/v1/graph-runs", initial_command)
    assert initial["outcome"]["status"] == "accepted"
    parent_run = e.active_run = initial["outcome"]["committed"]["object_id"]
    policy = {"parent": {"scope": e.scope, "plan_sha256": e.plan["sha256"], "definition_sha256": e.plan["document"]["lock"]["definition_sha256"]},
              "allowed_edits": [{"kind": "evaluator_swap", "edit_id": "release-upgrade", "target": {"scope_path": [], "node_id": "evaluate"},
                                  "expected_tool": e.locks["numeric-old"]["tool"], "replacement": e.locks["numeric-new"]}], "evaluator_call_limit": 16}
    e.planning_host(policy)

    def propose(name, cut, carried):
        request = {"scope": e.scope, "proposal_id": name, "policy": e.policy_reference, "predecessor": cut,
                   "edit_id": "release-upgrade", "successor_revision": 2, "carried": carried}
        result = e.call("planning", "/v1/topology-proposals", request)
        assert result["status"] == "proposed"
        assert e.call("planning", "/v1/topology-proposals", request) == result
        return result

    active = e.call("runtime", "/v3/graph-runs/" + parent_run)
    early = propose("before-terminal", {"run_id": parent_run, "plan_sha256": e.plan["sha256"], "revision": active["revision"]}, [])
    early_compiled = compile_proposal(e, early, "early")
    def admission(proposal, compiled, inputs):
        return e.command("graph.admit_draft_successor", {"plan_sha256": compiled["validation"]["plan_sha256"], "draft": compiled["draft"],
            "predecessor": proposal["request"]["predecessor"], "carried": proposal["request"]["carried"], "inputs": inputs, "budget": {"limit": 16}})
    early_command = admission(early, early_compiled, [{"port": "parameters", "value": value}])
    e.heartbeat("numeric-new")
    early_receipt = e.call("runtime", "/v1/graph-runs/draft-successors", early_command)
    assert early_receipt["outcome"]["reason_code"] == "predecessor_not_terminal"

    parent = run_graph(e, parent_run, "numeric-old")
    sources = {source["source"]["port"]: source for source in parent["cut"]["sources"]}
    carry = {"target_port": "parameters", "source": sources["parameters"]["source"], "expected_value_sha256": sources["parameters"]["value_sha256"]}
    proposal = propose("after-terminal", parent["cut"]["predecessor"], [carry])
    compiled = compile_proposal(e, proposal, "successor")
    command = admission(proposal, compiled, [])
    e.heartbeat("numeric-new")
    accepted = e.call("runtime", "/v1/graph-runs/draft-successors", command)
    assert accepted["outcome"]["status"] == "accepted"
    successor = run_graph(e, accepted["outcome"]["committed"]["object_id"], "numeric-new")
    lineage = e.call("runtime", "/v1/graph-runs/" + successor["run"] + "/lineage")
    assert lineage["predecessor"] == parent["cut"]["predecessor"] and lineage["carried"] == [carry]
    successor_sources = {source["source"]["port"]: source for source in successor["cut"]["sources"]}
    assert successor_sources["parameters"]["value_sha256"] == carry["expected_value_sha256"]
    # Output Artifact identities differ across runs, so compare actual exported bytes
    # through public graph output values, never just a matching value fingerprint.
    output_checks = []
    for record in (parent, successor):
        outputs = record["completion"]["result"]["outcome"]["outputs"]
        result_value = next(item for item in outputs if item["port"] == "result")
        arithmetic = json.loads(e.read_bytes(result_value["artifact"]))
        assert arithmetic == {"schema_version": "1", "values": [5, 3, 1]}
        output_checks.append({"artifact": result_value["artifact"], "result": arithmetic})
    benchmark_bytes = Path(e.config["benchmark"]).read_bytes()
    benchmark = json.loads(benchmark_bytes)
    assert benchmark["status"] == "completed" and len(benchmark["pairs"]) == 10 and benchmark["paid_calls"] == 0
    benchmark_ref = e.publish(benchmark_bytes, e.evidence_schemas["benchmark"])
    handoff = {"profile": "synthetic-topology-handoff-v1", "scope": e.scope, "proposal": proposal,
        "compiled": compiled, "admission": accepted, "admission_command": command, "lineage": lineage,
        "parent": parent, "successor": successor, "arithmetic": output_checks, "premature": {"proposal": early, "receipt": early_receipt},
        "benchmark": benchmark_ref, "comparison_applicability": "independent_numeric_search_engineering_only",
        "release_swap_fitness": "not_comparable_evaluator_changed", "scientific_authority": "not_established"}
    raw = common.encoded(handoff)
    artifact = e.publish(raw, e.evidence_schemas["handoff"])
    assert e.read_bytes(artifact) == raw
    for service in (e.planning, e.runtime, e.artifact):
        service.close()
        service.start()
        service.ready(e.tokens["admin"])
    assert e.call("planning", "/v1/topology-proposals/after-terminal") == proposal
    assert e.call("runtime", "/v1/graph-runs/draft-successors", command) == accepted
    assert e.call("runtime", "/v1/graph-runs/draft-successors", early_command) == early_receipt
    assert e.call("runtime", "/v1/graph-runs", initial_command) == initial
    assert e.call("runtime", "/v1/graph-runs/" + successor["run"] + "/lineage") == lineage
    assert e.read_bytes(artifact) == raw and e.read_bytes(benchmark_ref) == benchmark_bytes
    for record in (parent, successor):
        assert e.call("runtime", "/v1/runs/" + record["run"] + "/completions/" + record["worker"]["operation_id"] + "/producer") == record["producer"]
    return {"handoff": artifact, "benchmark": benchmark_ref, "lineage": lineage, "parent_run": parent_run,
            "successor_run": successor["run"], "premature_reason": early_receipt["outcome"]["reason_code"],
            "proposal": proposal["reference"], "restarted_owners": ["planning", "runtime", "artifact"], "paid_calls": 0}


def main():
    assert all(importlib.util.find_spec(name) is None for name in ("sqlalchemy", "amphora_campaign_runtime", "amphora_agent_planning", "amphora_data_artifacts"))
    config = json.loads(Path(sys.argv[1]).read_bytes())
    root = Path(config["evidence"])
    root.mkdir(parents=True, exist_ok=False)
    e = environment.Environment(config, root)
    try:
        e.setup()
        result = scenario(e)
        evidence = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed", "scope": e.scope,
            "result": result, "registry": e.registry_records, "packages": config["packages"],
            "limits": ["Declared image fixture pins; Windows processes, not image deployment", "Registry capacity is synthetic fixture metadata", "No scientific or model-quality claim"]}
        (root / "evidence.json").write_bytes(common.encoded(evidence))
        print("Public topology handoff passed; paid calls0", flush=True)
    finally:
        e.close()


if __name__ == "__main__":
    main()
