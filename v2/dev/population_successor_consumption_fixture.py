"""Actual accepted successor slicing and numerical-method consumption."""
import copy
import json
import subprocess

from amphora_contracts_population_steps import PopulationMemberSlice
from verify_retention_closure_installation import write


def decorate_successor_consumption(definition, descriptor):
    body = definition["body"]
    nodes = list(body["nodes"][:-1])
    adapter = {"kind": "invoke", "node_id": "successor_slice_request", "tool": descriptor["tool"]["binding"],
        "inputs": [{"port": "parameters", "source": {"kind": "output", "node_id": "prepare_successor", "port": "result"}}],
        "timeout_seconds": 3600, "checkpoint": None}
    sliced = copy.deepcopy(next(node for node in nodes if node["node_id"] == "slice"))
    sliced["node_id"] = "successor_slice"
    sliced["inputs"][0]["source"]["node_id"] = "successor_slice_request"
    project = copy.deepcopy(next(node for node in nodes if node["node_id"] == "candidate_contexts"))
    project.update(node_id="successor_contexts")
    project["source"]["node_id"] = "successor_slice"
    scatter = copy.deepcopy(next(node for node in nodes if node["node_id"] == "evaluate"))
    scatter.update(node_id="successor_evaluate")
    scatter["collection"]["node_id"] = "successor_contexts"
    nodes.extend((adapter, sliced, project, scatter))
    nodes.append({"kind": "finish", "node_id": "finish", "outputs": [{"port": "result",
        "source": {"kind": "output", "node_id": "successor_evaluate", "port": "result"}}]})
    body["nodes"] = nodes
    body["outputs"][0]["value_type"] = scatter["output"]["value_type"]
    body["edges"] = [{"source": a["node_id"], "target": b["node_id"], "route": "next"} for a,b in zip(nodes,nodes[1:])]


def consume_successor(fixture, run, worker_config, method_fixture, call, command, read):
    completions = []
    for operation in ("prepare-successor-slice", "slice"):
        for _ in range(32):
            call(fixture.runtime_port, "/v1/graph-runs/advance", command("graph.advance", {"run_id": run, "max_transitions": 32}))
            state = call(fixture.runtime_port, "/v1/runs/"+run)
            if any(item["status"] == "queued" for item in state["activations"]):
                break
        else:
            raise AssertionError("Successor consumption did not become ready")
        result = subprocess.run([str(fixture.python), "-I", "-m", "amphora_evolution_search", "population-worker",
            "--operation", operation, "--config", str(worker_config)], env=fixture.environment,
            capture_output=True, timeout=1200)
        (fixture.output/("population-successor-"+operation+".log")).write_bytes(result.stdout+result.stderr)
        assert result.returncode == 0, "Actual successor consumer failed; inspect consumer log"
        receipt = json.loads(result.stdout)
        assert receipt.get("outcome") == "succeeded", receipt
        completion = call(fixture.runtime_port, f"/v1/runs/{run}/completions/"+receipt["operation_id"])
        reservation = completion["retention_reservation_ids"][0]
        closure = call(fixture.data_port, "/v1/retention-closures/"+reservation)
        binding = closure["reservation"]["outcome"]["binding"]
        call(fixture.data_port, "/v1/reservations/confirm", command("artifacts.confirm", {"reservation_id": reservation,
            "intent_id": binding["intent"]["intent_id"], "runtime_receipt_id": receipt["operation_id"]}))
        completions.append(receipt["operation_id"])
    sliced = PopulationMemberSlice.model_validate_json(json.dumps(read(completion["result"]["outcome"]["outputs"][0]["artifact"])))
    assert sliced.generation.generation == 1 and sliced.complete and len(sliced.members) == 16
    evidence = method_fixture.run(run, sliced.members, worker_config, call, command, read,
        spent_before=26, log_prefix="population-successor-method", expected_generation=1)
    assert evidence["evaluated_members"] == 16 and evidence["spent"] == 42
    write(fixture.output/"population-successor-consumption-evidence.json", dict(status="passed",
        generation=1, contexts=16, evaluated_members=16, exact_values_verified=True,
        accepted_preparation_required=True, retained_slice_artifacts=closure["artifact_count"],
        run_status=evidence["run_status"], spent=evidence["spent"], provider_calls=0))
