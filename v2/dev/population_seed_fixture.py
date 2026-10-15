"""Actual installed seed primitive; declared methods are retained, not executed."""

import hashlib
import json
import subprocess
import time
from pathlib import Path

from amphora_contracts_population import (
    BirthManifest, BirthPage, CandidateBirth, EvaluationDeclarationManifest, EvaluationSlotPage,
    MembershipManifest, MembershipPage, PopulationSpecification,
    candidate_birth_schema, population_record_schema, population_specification_schema,
    membership_manifest_schema, membership_page_schema,
)
from amphora_contracts_population_steps import (
    PopulationCandidateContext, PopulationMemberSlice, PopulationSliceRequest,
    PreparedPopulationGeneration, SeedPopulationRequest, population_step_schema,
)
from amphora_contracts_search import ImplementationPin

from verify_retention_closure_installation import ROOT, request, write
from population_method_fixture import MethodFixture


def verify(output, python, ports, environment, scope, call, command, start, stop, *, with_slice=False, method_operation=None, inspect_inputs=False):
    data_port, runtime_port = ports
    descriptor_result = subprocess.run([str(python), "-I", "-m", "amphora_evolution_search", "population-describe",
        "--operation", "seed", "--image-sha256", "f" * 64], capture_output=True, timeout=120)
    assert descriptor_result.returncode == 0, "Installed population descriptor failed"
    descriptor = json.loads(descriptor_result.stdout)
    write(output / "population-seed-release.json", descriptor)
    slice_descriptor = None
    if with_slice:
        result = subprocess.run([str(python), "-I", "-m", "amphora_evolution_search", "population-describe",
            "--operation", "slice", "--image-sha256", "f" * 64], capture_output=True, timeout=120)
        assert result.returncode == 0, "Installed slice descriptor failed"
        slice_descriptor = json.loads(result.stdout)
        write(output / "population-slice-release.json", slice_descriptor)
    method_fixture = None if method_operation is None else MethodFixture(output, python, scope, environment, ports, method_operation)
    data = json.loads((output / "data.json").read_bytes())
    models = (
        (PopulationSpecification, population_specification_schema()),
        (CandidateBirth, candidate_birth_schema()), (BirthPage, population_record_schema("population.birth-page")),
        (BirthManifest, population_record_schema("population.birth-manifest")),
        (MembershipPage, membership_page_schema()), (MembershipManifest, membership_manifest_schema()),
        (EvaluationSlotPage, population_record_schema("population.evaluation-slot-page")),
        (EvaluationDeclarationManifest, population_record_schema("population.evaluation-declarations")),
        (PreparedPopulationGeneration, population_step_schema("population-step.prepared")),
        (SeedPopulationRequest, population_step_schema("population-step.seed")),
    )
    if with_slice:
        models += ((PopulationSliceRequest, population_step_schema("population-step.slice-request")),
                   (PopulationMemberSlice, population_step_schema("population-step.member-slice")),
                   (PopulationCandidateContext, population_step_schema("population-step.candidate-context")))
    if method_fixture is not None:
        models += method_fixture.models
    for index, (model, ref) in enumerate(models):
        schema = model.model_json_schema(mode="validation")
        schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"urn:amphora:{ref.schema_id}:1:validation"})
        raw = (json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()
        assert hashlib.sha256(raw).hexdigest() == ref.sha256
        name = "population-schema-" + str(index) + ".json"
        (output / name).write_bytes(raw)
        data["profiles"].append({"media_type": "application/json", **ref.model_dump(), "schema_path": name})
    # Genuine explicitly configured fixture schema, not an invented published hash.
    # This primitive does not admit/execute the specification's declared method graph.
    raw = b'{"type":"object","additionalProperties":true}'
    (output / "population-fixture-context.json").write_bytes(raw)
    context_schema = {"schema_id": "fixture.population-context", "version": "1", "sha256": hashlib.sha256(raw).hexdigest()}
    data["profiles"].append({"media_type": "application/json", **context_schema, "schema_path": "population-fixture-context.json"})
    worker = {"actor_id": "population-worker", "scope": scope, "token_env": "QUAL_WORKER_TOKEN"}
    environment["QUAL_WORKER_TOKEN"] = "w" * 32
    environment["QUAL_CURSOR_KEY"] = "c" * 64
    data["principals"].append({**worker, "actions": ["read", "upload", "finalize"]})
    write(output / "data.json", data)
    stop("runtime")
    stop("data")
    start("data", Path(environment["QUAL_DATA_PYTHON"]), data_port, environment)

    def publish(record, schema, parents=()):
        raw = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
        content = {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw), "media_type": "application/json", "schema_ref": schema}
        payload = {"content": content}
        if parents:
            payload["declaration"] = {"transformation": {"transformation_id": "fixture.population", "version": "1", "sha256": "e" * 64}, "inputs": parents}
        begin = call(data_port, "/v1/derived-uploads" if parents else "/v1/uploads", command(
            "artifacts.begin_derived_upload" if parents else "artifacts.begin_upload", payload))
        upload = begin["upload"] if parents else begin
        import http.client
        connection = http.client.HTTPConnection("127.0.0.1", data_port, timeout=20)
        try:
            connection.request("PUT", "/v1/uploads/" + upload["upload_id"] + "/content", raw, {"Authorization": "Bearer " + "q" * 32})
            response = connection.getresponse()
            assert response.status == 200, response.read()
            response.read()
        finally:
            connection.close()
        return call(data_port, "/v1/artifacts/finalize", command("artifacts.finalize", {
            "upload_id": upload["upload_id"], "content": upload["content"]}))["artifact"]

    def read(reference):
        import http.client
        connection = http.client.HTTPConnection("127.0.0.1", data_port, timeout=20)
        try:
            connection.request("GET", "/v1/artifacts/" + reference["artifact_id"] + "/content",
                headers={"Authorization": "Bearer " + "q" * 32})
            response = connection.getresponse()
            raw = response.read()
            assert response.status == 200
            assert len(raw) == reference["size_bytes"] and hashlib.sha256(raw).hexdigest() == reference["sha256"]
            return json.loads(raw)
        finally:
            connection.close()

    context = publish({"scope": "synthetic-numeric-primitive-only", "method_graph_executed": method_fixture is not None}, context_schema)
    original = json.loads((ROOT / "tools/evolution_search/tests/population/specification/fixtures/specification.json").read_bytes())
    original["scope"], original["representation"] = scope, candidate_birth_schema().model_dump()
    original["implementations"] = [ImplementationPin(name="numeric-population-steps",
        version=descriptor["tool"]["binding"]["release"], sha256="f" * 64).model_dump()]
    original["budget"].update(population_size=16, dispatch_slice=8, successor_generations=0)
    original["method_graph"]["definition"] = context
    for method in original["method_graph"]["methods"]:
        method["conditions"] = context
    original["assembly"]["policy"] = original["constraints"] = context
    original["context"], original["knowledge"] = [], []
    def shape(direction, release=descriptor):
        port = release["tool"][direction][0]
        return {"kind": "artifact", "schema_ref": port["schema_ref"],
            "representation": port["representation"], "unit": port["unit"], "media_type": "application/json"}
    definition = {"schema_version": "2", "profile": "deterministic-v1", "campaign_id": "population-seed-primitive",
        "revision": 1, "scope": scope, "context": [], "body": {
            "inputs": [{"name": "parameters", "value_type": shape("inputs")}],
            "outputs": [{"name": "result", "value_type": shape("outputs")}],
            "nodes": [{"kind": "invoke", "node_id": "seed", "tool": descriptor["tool"]["binding"],
                "inputs": [{"port": "parameters", "source": {"kind": "input", "name": "parameters"}}],
                "timeout_seconds": 3600, "checkpoint": None},
                {"kind": "finish", "node_id": "finish", "outputs": [{"port": "result", "source": {"kind": "output", "node_id": "seed", "port": "result"}}]}],
            "edges": [{"source": "seed", "target": "finish", "route": "next"}]}}
    if with_slice:
        definition.update(schema_version="4", profile="deterministic-v3", campaign_id="population-seed-slice-primitives")
        body = definition["body"]
        body["outputs"][0]["value_type"] = shape("outputs", slice_descriptor)
        body["nodes"] = [body["nodes"][0], {
            "kind": "artifact_materialize", "node_id": "slice_request", "fields": [
                {"name": "schema_version", "mode": "inline", "source": {"kind": "string", "value": "1"}},
                {"name": "prepared", "mode": "references", "source": {"kind": "output", "node_id": "seed", "port": "result"}},
                {"name": "start_index", "mode": "inline", "source": {"kind": "integer", "value": 0, "unit": "1"}},
                {"name": "limit", "mode": "inline", "source": {"kind": "integer", "value": 8, "unit": "1"}}],
            "output": {"name": "result", "value_type": shape("inputs", slice_descriptor)},
            "limits": {"max_items": 32, "max_artifacts": 4, "max_bytes": 262144, "timeout_seconds": 120}},
            {"kind": "invoke", "node_id": "slice", "tool": slice_descriptor["tool"]["binding"],
             "inputs": [{"port": "parameters", "source": {"kind": "output", "node_id": "slice_request", "port": "result"}}],
             "timeout_seconds": 3600, "checkpoint": None},
            {"kind": "finish", "node_id": "finish", "outputs": [{"port": "result",
                "source": {"kind": "output", "node_id": "slice", "port": "result"}}]}]
        body["edges"] = [{"source": left["node_id"], "target": right["node_id"], "route": "next"}
                         for left, right in zip(body["nodes"], body["nodes"][1:])]
    if method_fixture is not None:
        method_fixture.decorate(definition)
    write(output / "population-seed-graph.json", definition)
    lock = {"schema_version": "1", "tool": descriptor["tool"]["binding"], "checkpoint_schema": None,
        "descriptor_sha256": hashlib.sha256(json.dumps({"profile": "amphora-tool-release-v1", "descriptor": descriptor},
            sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest(),
        "input_schemas": [{"port": "parameters", "schema_ref": descriptor["tool"]["inputs"][0]["schema_ref"]}],
        "output_schemas": [{"port": "result", "schema_ref": descriptor["tool"]["outputs"][0]["schema_ref"]}]}
    runtime = json.loads((output / "runtime.json").read_bytes())
    runtime["principals"][0]["actions"].append("inspect_receipts")
    runtime["principals"].append({**worker, "actions": ["claim", "renew", "complete", "read"]})
    runtime["inspection"] = {"cursor_key_env": "QUAL_CURSOR_KEY"}
    runtime["graphs"] = [{"definition": "population-seed-graph.json", "releases": [{"descriptor": "population-seed-release.json", "lock": lock}],
        "schemas": [{"schema_ref": ref, "path": "population-schema-" + str(index) + ".json"}
            for index, (_, schema) in enumerate(models) for ref in [schema.model_dump()] if ref["sha256"] in {
                descriptor["tool"]["inputs"][0]["schema_ref"]["sha256"], descriptor["tool"]["outputs"][0]["schema_ref"]["sha256"]}]}]
    if with_slice:
        slice_lock = {"schema_version": "1", "tool": slice_descriptor["tool"]["binding"], "checkpoint_schema": None,
            "descriptor_sha256": hashlib.sha256(json.dumps({"profile": "amphora-tool-release-v1", "descriptor": slice_descriptor},
                sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest(),
            "input_schemas": [{"port": "parameters", "schema_ref": slice_descriptor["tool"]["inputs"][0]["schema_ref"]}],
            "output_schemas": [{"port": "result", "schema_ref": slice_descriptor["tool"]["outputs"][0]["schema_ref"]}]}
        runtime["graphs"][0]["releases"].append({"descriptor": "population-slice-release.json", "lock": slice_lock})
        runtime["graphs"][0]["schemas"].extend({"schema_ref": schema.model_dump(), "path": "population-schema-" + str(index) + ".json"}
            for index, (_, schema) in enumerate(models) if schema.sha256 in {
                slice_descriptor["tool"]["inputs"][0]["schema_ref"]["sha256"], slice_descriptor["tool"]["outputs"][0]["schema_ref"]["sha256"]})
        runtime["bindings"] = {"endpoint": f"http://127.0.0.1:{data_port}", "token_env": "QUAL_TOKEN"}
    if method_fixture is not None:
        method_fixture.configure(runtime, models)
    write(output / "runtime.json", runtime)
    ready = start("runtime", Path(environment["QUAL_RUNTIME_PYTHON"]), runtime_port, environment)
    if method_fixture is not None:
        definition_reference = publish(method_fixture.definition, method_fixture.graph_schema.model_dump(), [context])
        method_fixture.pin(original, definition_reference, ready["plans"]["population-primary-method"])
    specification = publish(PopulationSpecification.model_validate_json(json.dumps(original)).model_dump(mode="json"),
        population_specification_schema().model_dump(), [context, original["method_graph"]["definition"]]
        if method_fixture is not None else [context])
    source = publish(SeedPopulationRequest(schema_version="1", specification=specification).model_dump(mode="json"),
        population_step_schema("population-step.seed").model_dump(), [specification])
    admitted = call(runtime_port, "/v1/graph-runs", command("graph.admit", {"plan_sha256": ready["plan_sha256"],
        "inputs": [{"port": "parameters", "value": {"kind": "artifact", "representation": "population-reference-v1", "unit": "1", "artifact": source}}],
        "budget": {"limit": 10 if method_fixture is not None else 2 if with_slice else 1}}))
    run = admitted["outcome"]["committed"]["object_id"]
    worker_config = {"actor_id": "population-worker", "scope": scope, "run_id": run, "image_sha256": "f" * 64,
        "runtime": {"endpoint": f"http://127.0.0.1:{runtime_port}", "token_env": "QUAL_WORKER_TOKEN"},
        "artifacts": {"endpoint": f"http://127.0.0.1:{data_port}", "token_env": "QUAL_WORKER_TOKEN"}, "lease_seconds": 60}
    write(output / "population-worker.json", worker_config)
    result = subprocess.run([str(python), "-I", "-m", "amphora_evolution_search", "population-worker", "--operation", "seed",
        "--config", str(output / "population-worker.json")], env=environment, capture_output=True, timeout=1200)
    (output / "population-worker.log").write_bytes(result.stdout + result.stderr)
    if result.returncode:
        write(output / "population-failure-state.json", call(runtime_port, "/v1/runs/" + run))
    assert result.returncode == 0, "Actual population worker failed; inspect population-worker.log"
    receipt = json.loads(result.stdout)
    assert receipt["outcome"] == "succeeded"
    completion = call(runtime_port, f"/v1/runs/{run}/completions/" + receipt["operation_id"])
    prepared = completion["result"]["outcome"]["outputs"][0]["artifact"]
    reservation = completion["retention_reservation_ids"][0]
    closure = call(data_port, "/v1/retention-closures/" + reservation)
    assert closure["artifact_count"] >= 16 + 4
    binding = closure["reservation"]["outcome"]["binding"]
    call(data_port, "/v1/reservations/confirm", command("artifacts.confirm", {"reservation_id": reservation,
        "intent_id": binding["intent"]["intent_id"], "runtime_receipt_id": receipt["operation_id"]}))
    # Explicitly prove that the worker principal has no retention grant.
    import http.client
    connection = http.client.HTTPConnection("127.0.0.1", data_port, timeout=10)
    try:
        connection.request("GET", "/v1/retention-closures/" + reservation, headers={"Authorization": "Bearer " + "w" * 32})
        response = connection.getresponse()
        assert response.status == 403
        response.read()
    finally:
        connection.close()
    advance = command("graph.advance", {"run_id": run, "max_transitions": 10})
    for _ in range(16):
        advanced = call(runtime_port, "/v1/graph-runs/advance", advance)
        state = call(runtime_port, "/v1/runs/" + run)
        if not with_slice or any(a["status"] == "queued" for a in state["activations"]):
            break
        assert advanced["outcome"]["status"] != "rejected", advanced
        if advanced["outcome"]["status"] != "pending":
            advance = command("graph.advance", {"run_id": run, "max_transitions": 10})
        time.sleep(.1)
    else:
        write(output / "population-materialization-state.json", state)
        raise AssertionError("Slice materialization did not issue work within bounded coordinator passes")
    slice_evidence = method_evidence = None
    if with_slice:
        result = subprocess.run([str(python), "-I", "-m", "amphora_evolution_search", "population-worker", "--operation", "slice",
            "--config", str(output / "population-worker.json")], env=environment, capture_output=True, timeout=1200)
        (output / "population-slice-worker.log").write_bytes(result.stdout + result.stderr)
        if result.returncode:
            write(output / "population-slice-failure-state.json", call(runtime_port, "/v1/runs/" + run))
        assert result.returncode == 0, "Actual slice worker failed; inspect population-slice-worker.log"
        receipt = json.loads(result.stdout)
        assert receipt["outcome"] == "succeeded"
        completion = call(runtime_port, f"/v1/runs/{run}/completions/" + receipt["operation_id"])
        slice_reference = completion["result"]["outcome"]["outputs"][0]["artifact"]
        slice_reservation = completion["retention_reservation_ids"][0]
        slice_closure = call(data_port, "/v1/retention-closures/" + slice_reservation)
        binding = slice_closure["reservation"]["outcome"]["binding"]
        call(data_port, "/v1/reservations/confirm", command("artifacts.confirm", {
            "reservation_id": slice_reservation, "intent_id": binding["intent"]["intent_id"],
            "runtime_receipt_id": receipt["operation_id"]}))
        sliced = PopulationMemberSlice.model_validate_json(json.dumps(read(slice_reference)))
        assert sliced.generation.run_id == run and sliced.prepared.model_dump(mode="json") == prepared
        assert len(sliced.members) == 8 and sliced.start_index == 0 and sliced.next_index == 8 and not sliced.complete
        if method_fixture is not None:
            method_evidence = method_fixture.run(run, sliced.members, output / "population-worker.json", call, command, read)
        else:
            call(runtime_port, "/v1/graph-runs/advance", command("graph.advance", {"run_id": run, "max_transitions": 10}))
            final = call(runtime_port, "/v1/runs/" + run)
            assert final["status"] == "completed" and final["budget"]["spent"] == 2
        slice_evidence = {"members": 8, "next_index": 8, "complete": False,
            "same_run": True, "retained_artifacts": slice_closure["artifact_count"], "spent": 2}
    if inspect_inputs:
        from amphora_contracts_node_inputs import NodeInputObservation
        nodes = call(runtime_port, f"/v1/graph-observations/{run}/nodes")["nodes"]
        observations = {}
        for node in nodes:
            path = f"/v1/graph-observations/{run}/nodes/{node['activation_id']}/inputs"
            raw = call(runtime_port, path)
            observation = NodeInputObservation.model_validate_json(json.dumps(raw))
            assert observation.scope.model_dump(mode="json") == scope
            observations[path] = raw
        assert any(raw["invocation"] is not None for raw in observations.values())
        stop("runtime")
        start("runtime", Path(environment["QUAL_RUNTIME_PYTHON"]), runtime_port, environment)
        for path, raw in observations.items():
            assert call(runtime_port, path) == raw
        write(output / "node-inputs-evidence.json", {"status":"passed", "nodes":len(nodes),
            "original_inputs_survive_runtime_restart":True, "schema":"runtime-node-inputs-v1",
            "provider_calls":0})
    write(output / "population-seed-evidence.json", {"status": "passed", "population": 16,
        "worker_release": descriptor["tool"]["binding"]["release"], "retained_artifacts": closure["artifact_count"],
        "prepared": prepared, "worker_retention_grant": False, "provider_calls": 0,
        "slice": slice_evidence,
        "method": method_evidence,
        "scope": "Actual installed numerical primitives; full population/fitness/selection composition not executed"})
    print("Actual installed population seed" + ("/slice" if with_slice else "") + " accepted with complete closure; worker retention denied.", flush=True)
