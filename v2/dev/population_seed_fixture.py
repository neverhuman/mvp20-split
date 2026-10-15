"""Actual installed seed primitive; declared methods are retained, not executed."""

import hashlib
import json
import subprocess
from pathlib import Path

from amphora_contracts_population import (
    BirthManifest, BirthPage, CandidateBirth, EvaluationDeclarationManifest, EvaluationSlotPage,
    MembershipManifest, MembershipPage, PopulationSpecification,
    candidate_birth_schema, population_record_schema, population_specification_schema,
    membership_manifest_schema, membership_page_schema,
)
from amphora_contracts_population_steps import PreparedPopulationGeneration, SeedPopulationRequest, population_step_schema
from amphora_contracts_search import ImplementationPin

from verify_retention_closure_installation import ROOT, request, write


def verify(output, python, ports, environment, scope, call, command, start, stop):
    data_port, runtime_port = ports
    descriptor_result = subprocess.run([str(python), "-I", "-m", "amphora_evolution_search", "population-describe",
        "--operation", "seed", "--image-sha256", "f" * 64], capture_output=True, timeout=120)
    assert descriptor_result.returncode == 0, "Installed population descriptor failed"
    descriptor = json.loads(descriptor_result.stdout)
    write(output / "population-seed-release.json", descriptor)
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

    context = publish({"scope": "synthetic-seed-primitive-only", "method_graph_executed": False}, context_schema)
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
    specification = publish(PopulationSpecification.model_validate_json(json.dumps(original)).model_dump(mode="json"),
        population_specification_schema().model_dump(), [context])
    source = publish(SeedPopulationRequest(schema_version="1", specification=specification).model_dump(mode="json"),
        population_step_schema("population-step.seed").model_dump(), [specification])

    def shape(direction):
        return {"kind": "artifact", "schema_ref": descriptor["tool"][direction][0]["schema_ref"],
            "representation": "population-reference-v1", "unit": "1", "media_type": "application/json"}
    definition = {"schema_version": "2", "profile": "deterministic-v1", "campaign_id": "population-seed-primitive",
        "revision": 1, "scope": scope, "context": [], "body": {
            "inputs": [{"name": "parameters", "value_type": shape("inputs")}],
            "outputs": [{"name": "result", "value_type": shape("outputs")}],
            "nodes": [{"kind": "invoke", "node_id": "seed", "tool": descriptor["tool"]["binding"],
                "inputs": [{"port": "parameters", "source": {"kind": "input", "name": "parameters"}}],
                "timeout_seconds": 3600, "checkpoint": None},
                {"kind": "finish", "node_id": "finish", "outputs": [{"port": "result", "source": {"kind": "output", "node_id": "seed", "port": "result"}}]}],
            "edges": [{"source": "seed", "target": "finish", "route": "next"}]}}
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
    write(output / "runtime.json", runtime)
    ready = start("runtime", Path(environment["QUAL_RUNTIME_PYTHON"]), runtime_port, environment)
    admitted = call(runtime_port, "/v1/graph-runs", command("graph.admit", {"plan_sha256": ready["plan_sha256"],
        "inputs": [{"port": "parameters", "value": {"kind": "artifact", "representation": "population-reference-v1", "unit": "1", "artifact": source}}],
        "budget": {"limit": 1}}))
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
    call(runtime_port, "/v1/graph-runs/advance", command("graph.advance", {"run_id": run, "max_transitions": 10}))
    write(output / "population-seed-evidence.json", {"status": "passed", "population": 16,
        "worker_release": descriptor["tool"]["binding"]["release"], "retained_artifacts": closure["artifact_count"],
        "prepared": prepared, "worker_retention_grant": False, "provider_calls": 0,
        "scope": "Actual installed seed primitive only; declared method graph and full population composition not executed"})
    print("Actual installed population seed worker accepted with complete closure; worker retention denied.", flush=True)
