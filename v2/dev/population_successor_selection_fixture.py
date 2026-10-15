"""Actual global parent/offspring selection and cumulative accepted work counters."""
import copy
import json
import subprocess

from amphora_contracts_population import PopulationCheckpoint, PopulationSelectionReceipt, SelectionPage, FitnessManifest, FitnessPage
from amphora_contracts_population_steps import SelectPopulationRequest
from amphora_evolution_search.population_workers.payloads import SelectedPrimaryGeneration
from amphora_evolution_search.population_workers.capabilities import PopulationCapability
from population_method_fixture import shape
from verify_retention_closure_installation import write


def decorate_successor_selection(definition):
    body = definition["body"]
    nodes = list(body["nodes"][:-1])
    request = copy.deepcopy(next(node for node in nodes if node["node_id"] == "selection_request"))
    request["node_id"] = "successor_selection_request"
    request["inputs"][0]["source"]["node_id"] = "successor_assemble"
    select = copy.deepcopy(next(node for node in nodes if node["node_id"] == "select"))
    select["node_id"] = "successor_select"
    select["inputs"][0]["source"]["node_id"] = "successor_selection_request"
    nodes.extend((request, select))
    nodes.append(dict(kind="finish", node_id="finish", outputs=[dict(port="result",
        source=dict(kind="output", node_id="successor_select", port="result"))]))
    body["nodes"] = nodes
    body["outputs"][0]["value_type"] = shape(PopulationCapability("select-primary").descriptor("f"*64).model_dump(mode="json"), "outputs")
    body["edges"] = [dict(source=a["node_id"], target=b["node_id"], route="next") for a,b in zip(nodes,nodes[1:])]


def run_successor_selection(fixture, run, worker_config, fitted, call, command, read):
    for operation in ("prepare-selection", "select-primary"):
        for _ in range(32):
            call(fixture.runtime_port, "/v1/graph-runs/advance", command("graph.advance", dict(run_id=run, max_transitions=32)))
            state = call(fixture.runtime_port, "/v1/runs/"+run)
            if any(item["status"] == "queued" for item in state["activations"]): break
        else: raise AssertionError("Successor selection did not become ready")
        result = subprocess.run([str(fixture.python), "-I", "-m", "amphora_evolution_search", "population-worker",
            "--operation", operation, "--config", str(worker_config)], env=fixture.environment, capture_output=True, timeout=1200)
        (fixture.output/("population-successor-"+operation+".log")).write_bytes(result.stdout+result.stderr)
        assert result.returncode == 0, "Actual successor selection failed; inspect log"
        receipt = json.loads(result.stdout); assert receipt.get("outcome") == "succeeded", receipt
        completion = call(fixture.runtime_port, f"/v1/runs/{run}/completions/"+receipt["operation_id"])
        root = completion["result"]["outcome"]["outputs"][0]["artifact"]
        if operation == "prepare-selection":
            request = SelectPopulationRequest.model_validate_json(json.dumps(read(root)))
            assert request.predecessor == fitted.generation.predecessor
        reservation = completion["retention_reservation_ids"][0]
        closure = call(fixture.data_port, "/v1/retention-closures/"+reservation)
        binding = closure["reservation"]["outcome"]["binding"]
        call(fixture.data_port, "/v1/reservations/confirm", command("artifacts.confirm", dict(reservation_id=reservation,
            intent_id=binding["intent"]["intent_id"], runtime_receipt_id=receipt["operation_id"])))
    selected = SelectedPrimaryGeneration.model_validate_json(json.dumps(read(root)))
    checkpoint = PopulationCheckpoint.model_validate_json(json.dumps(read(selected.checkpoint.model_dump(mode="json"))))
    selection = PopulationSelectionReceipt.model_validate_json(json.dumps(read(selected.selection.model_dump(mode="json"))))
    ranks = [row for page in selection.pages for row in SelectionPage.model_validate_json(json.dumps(read(page.artifact.model_dump(mode="json")))).members]
    manifest = FitnessManifest.model_validate_json(json.dumps(read(fitted.fitness.model_dump(mode="json"))))
    fitness = [row for page in manifest.pages for row in FitnessPage.model_validate_json(json.dumps(read(page.artifact.model_dump(mode="json")))).records]
    scores = {row.candidate_id: row.outcome.objectives[0].value.value for row in fitness if row.outcome.status == "evaluated"}
    unavailable = {row.candidate_id for row in fitness if row.outcome.status == "unavailable"}
    assert len(ranks) == len(fitness) == 32 and len(selection.selected) == 16
    assert {row.candidate_id for row in ranks if row.status == "excluded"} == unavailable
    assert not set(selection.selected) & unavailable
    assert max(scores[key] for key in selection.selected) <= min(value for key,value in scores.items() if key not in selection.selected)
    assert checkpoint.generation == fitted.generation and checkpoint.generation.predecessor == request.predecessor
    assert checkpoint.progress.evaluations_issued == checkpoint.progress.evaluations_terminal == 32
    assert checkpoint.progress.attempts_issued == 47 and checkpoint.rng.counter == 112
    assert checkpoint.progress.unchanged_front_generations in {0,1}
    snapshot = call(fixture.runtime_port, f"/v1/graph-observations/{run}/nodes")
    assert checkpoint.progress.activations_created == snapshot["snapshot"]["node_count"]
    assert selected.stopped and selected.stop_reason == "generation_budget"
    for _ in range(16):
        call(fixture.runtime_port, "/v1/graph-runs/advance", command("graph.advance", dict(run_id=run, max_transitions=32)))
        state = call(fixture.runtime_port, "/v1/runs/"+run)
        if state["status"] == "completed": break
    assert state["status"] == "completed" and state["budget"]["spent"] == 47, state
    write(fixture.output/"population-successor-selection-evidence.json", dict(status="passed", generation=1,
        pool_members=32, selected=16, excluded=len(unavailable), global_cost_order_verified=True,
        logical_evaluations=32, attempts_issued=47, activations_created=checkpoint.progress.activations_created,
        rng_counter=checkpoint.rng.counter, unchanged_front_generations=checkpoint.progress.unchanged_front_generations,
        stop_reason=selected.stop_reason, retained_artifacts=closure["artifact_count"], run_status="completed", spent=47, provider_calls=0))
