"""Actual successor collection and parent-preserving whole-pool fitness."""
import copy
import json
import math
import subprocess

from amphora_contracts_population import CandidateBirth, FitnessManifest, FitnessPage, MembershipManifest, MembershipPage
from amphora_contracts_population_steps import population_step_schema
from amphora_evolution_search.population_workers.payloads import FittedPrimaryGeneration, SelectedPrimaryGeneration
from verify_retention_closure_installation import write


def decorate_successor_fitness(definition, descriptor):
    body = definition["body"]
    nodes = list(body["nodes"][:-1])
    scope_input = copy.deepcopy(next(item for item in body["inputs"] if item["name"] == "method_scope_path"))
    scope_input["name"] = "successor_method_scope_path"
    body["inputs"].append(scope_input)
    request = copy.deepcopy(next(node for node in nodes if node["node_id"] == "collection_request"))
    request["node_id"] = "successor_collection_request"
    for field in request["fields"]:
        if field["name"] == "prepared":
            field["name"] = "sliced"
            field["source"]["node_id"] = "successor_slice"
        if field["name"] == "method_scope_path": field["source"]["name"] = "successor_method_scope_path"
    from population_method_fixture import shape
    request["output"]["value_type"] = shape(descriptor,"inputs")
    adapter = dict(kind="invoke",node_id="successor_collect_adapter",tool=descriptor["tool"]["binding"],
        inputs=[dict(port="parameters",source=dict(kind="output",node_id="successor_collection_request",port="result"))],
        timeout_seconds=3600,checkpoint=None)
    collect = copy.deepcopy(next(node for node in nodes if node["node_id"] == "collect"))
    collect["node_id"] = "successor_collect"
    collect["inputs"][0]["source"]["node_id"] = "successor_collect_adapter"
    assemble = copy.deepcopy(next(node for node in nodes if node["node_id"] == "assemble"))
    assemble["node_id"] = "successor_assemble"
    assemble["inputs"][0]["source"]["node_id"] = "successor_collect"
    nodes.extend((request, adapter, collect, assemble))
    nodes.append(dict(kind="finish", node_id="finish", outputs=[dict(port="result",
        source=dict(kind="output", node_id="successor_assemble", port="result"))]))
    body["nodes"] = nodes
    # The registered assembly output type equals prepare-selection's input type.
    from amphora_evolution_search.population_workers.capabilities import PopulationCapability
    descriptor = PopulationCapability("assemble-primary").descriptor("f"*64)
    body["outputs"][0]["value_type"] = dict(kind="artifact", schema_ref=descriptor.tool.outputs[0].schema_ref.model_dump(),
        representation="population-reference-v1", unit="1", media_type="application/json")
    body["edges"] = [dict(source=a["node_id"], target=b["node_id"], route="next") for a,b in zip(nodes,nodes[1:])]


def run_successor_fitness(fixture, run, worker_config, detail, call, command, read):
    failure = getattr(fixture, "failure", False)
    selected = SelectedPrimaryGeneration.model_validate_json(json.dumps(read(detail.source_selected.model_dump(mode="json"))))
    def fitness_rows(reference):
        manifest = FitnessManifest.model_validate_json(json.dumps(read(reference)))
        rows = [row for page in manifest.pages for row in FitnessPage.model_validate_json(
            json.dumps(read(page.artifact.model_dump(mode="json")))).records]
        return manifest, {row.candidate_id: row for row in rows}
    _, old = fitness_rows(selected.fitness.model_dump(mode="json"))
    for operation in ("prepare-successor-collection", "collect-primary", "assemble-primary"):
        for _ in range(32):
            call(fixture.runtime_port, "/v1/graph-runs/advance", command("graph.advance", dict(run_id=run, max_transitions=32)))
            state = call(fixture.runtime_port, "/v1/runs/"+run)
            if any(item["status"] == "queued" for item in state["activations"]): break
        else: raise AssertionError("Successor fitness step never became ready")
        result = subprocess.run([str(fixture.python), "-I", "-m", "amphora_evolution_search", "population-worker",
            "--operation", operation, "--config", str(worker_config)], env=fixture.environment, capture_output=True, timeout=1200)
        (fixture.output/("population-successor-"+operation+".log")).write_bytes(result.stdout+result.stderr)
        assert result.returncode == 0, "Actual successor collection/fitness failed; inspect log"
        receipt = json.loads(result.stdout); assert receipt.get("outcome") == "succeeded", receipt
        completion = call(fixture.runtime_port, f"/v1/runs/{run}/completions/"+receipt["operation_id"])
        reservation = completion["retention_reservation_ids"][0]
        closure = call(fixture.data_port, "/v1/retention-closures/"+reservation)
        binding = closure["reservation"]["outcome"]["binding"]
        call(fixture.data_port, "/v1/reservations/confirm", command("artifacts.confirm", dict(reservation_id=reservation,
            intent_id=binding["intent"]["intent_id"], runtime_receipt_id=receipt["operation_id"])))
    fitted = FittedPrimaryGeneration.model_validate_json(json.dumps(read(completion["result"]["outcome"]["outputs"][0]["artifact"])))
    manifest, rows = fitness_rows(fitted.fitness.model_dump(mode="json"))
    pool = MembershipManifest.model_validate_json(json.dumps(read(fitted.pool.model_dump(mode="json"))))
    members = [member for page in pool.pages for member in MembershipPage.model_validate_json(
        json.dumps(read(page.artifact.model_dump(mode="json")))).members]
    parents = [member for member in members if member.source == "parent"]
    offspring = [member for member in members if member.source == "offspring"]
    assert len(parents) == len(offspring) == 16 and len(rows) == pool.member_count == manifest.member_count == 32
    assert len(manifest.observations) == 2 and fitted.generation.generation == 1
    unavailable = [row for row in rows.values() if row.outcome.status == "unavailable"]
    assert len(unavailable) == (1 if failure else 0)
    assert all(row.generation.generation == 1 and row.outcome.reason_code == "required_method_unavailable"
        for row in unavailable)
    for parent in parents: assert rows[parent.candidate_id] == old[parent.candidate_id]
    for member in members:
        row = rows[member.candidate_id]
        assert row.generation.generation == (0 if member.source == "parent" else 1)
        if row.outcome.status != "evaluated": continue
        birth = CandidateBirth.model_validate_json(json.dumps(read(member.birth.model_dump(mode="json"))))
        assert row.outcome.objectives[0].value.value == math.fsum(g*g for g in birth.genes)
    for _ in range(16):
        call(fixture.runtime_port, "/v1/graph-runs/advance", command("graph.advance", dict(run_id=run, max_transitions=32)))
        state = call(fixture.runtime_port, "/v1/runs/"+run)
        if state["status"] == "completed" or (fixture.selection and any(a["status"] == "queued" for a in state["activations"])): break
    assert state["status"] == ("running" if fixture.selection else "completed") and state["budget"]["spent"] == 45, state
    write(fixture.output/"population-successor-fitness-evidence.json", dict(status="passed", generation=1,
        parents=16, offspring=16, fitness_records=32, original_parent_records_preserved=True,
        available=sum(row.outcome.status == "evaluated" for row in rows.values()), unavailable=len(unavailable),
        successor_required_failure=failure, observation_sources=2,
        retained_artifacts=closure["artifact_count"], run_status=state["status"], spent=45, provider_calls=0))
    if fixture.selection:
        from population_successor_selection_fixture import run_successor_selection
        run_successor_selection(fixture, run, worker_config, fitted, call, command, read)
