"""Installed numerical method/scatter primitive; no private owner imports."""

import hashlib
import json
import math
import subprocess

from amphora_contracts_campaigns import ExecutableCampaignV4
from amphora_contracts_core import SchemaRef
from amphora_contracts_population import CandidateBirth
from amphora_contracts_population_steps import PopulationCandidateContext, population_step_schema
from amphora_contracts_search import ObjectiveValue


def shape(release, direction):
    port = release["tool"][direction][0]
    return {"kind": "artifact", "schema_ref": port["schema_ref"], "representation": port["representation"],
            "unit": port["unit"], "media_type": "application/json"}


def release_lock(descriptor):
    digest = hashlib.sha256(json.dumps({"profile": "amphora-tool-release-v1", "descriptor": descriptor},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    return {"schema_version": "1", "tool": descriptor["tool"]["binding"], "descriptor_sha256": digest,
        "checkpoint_schema": None,
        "input_schemas": [{"port": "parameters", "schema_ref": descriptor["tool"]["inputs"][0]["schema_ref"]}],
        "output_schemas": [{"port": "result", "schema_ref": descriptor["tool"]["outputs"][0]["schema_ref"]}]}


class MethodFixture:
    def __init__(self, output, python, scope, environment, ports, operation):
        self.output, self.python, self.scope, self.environment = output, python, scope, environment
        self.data_port, self.runtime_port = ports
        self.operation = operation
        result = subprocess.run([str(python), "-I", "-m", "amphora_evolution_search", "population-describe",
            "--operation", operation, "--image-sha256", "f" * 64], capture_output=True, timeout=120)
        assert result.returncode == 0, "Installed method descriptor failed"
        self.descriptor = json.loads(result.stdout)
        (output / "population-method-release.json").write_text(json.dumps(self.descriptor), encoding="utf-8")
        schema = ExecutableCampaignV4.model_json_schema(mode="validation")
        schema.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:amphora:fixture.population-method-graph:1:validation"})
        raw = (json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()
        self.graph_schema = SchemaRef(schema_id="fixture.population-method-graph", version="1", sha256=hashlib.sha256(raw).hexdigest())
        self.models = ((ObjectiveValue, SchemaRef.model_validate(self.descriptor["tool"]["outputs"][0]["schema_ref"])),
                       (ExecutableCampaignV4, self.graph_schema))
        self.definition = {"schema_version": "4", "profile": "deterministic-v3", "campaign_id": "population-primary-method",
            "revision": 1, "scope": scope, "context": [], "body": {
                "inputs": [{"name": "candidate", "value_type": shape(self.descriptor, "inputs")}],
                "outputs": [{"name": "result", "value_type": shape(self.descriptor, "outputs")}],
                "nodes": [{"kind": "invoke", "node_id": "cost", "tool": self.descriptor["tool"]["binding"],
                    "inputs": [{"port": "parameters", "source": {"kind": "input", "name": "candidate"}}],
                    "timeout_seconds": 3600, "checkpoint": None},
                    {"kind": "finish", "node_id": "finish", "outputs": [{"port": "result",
                        "source": {"kind": "output", "node_id": "cost", "port": "result"}}]}],
                "edges": [{"source": "cost", "target": "finish", "route": "next"}]}}
        (output / "population-method-graph.json").write_text(json.dumps(self.definition), encoding="utf-8")

    def decorate(self, definition):
        body = definition["body"]
        contexts = {"kind": "collection", "item": shape(self.descriptor, "inputs"), "max_items": 32, "missing_slots": False}
        results = {"kind": "collection", "item": shape(self.descriptor, "outputs"), "max_items": 32, "missing_slots": False}
        project = {"kind": "artifact_project", "node_id": "candidate_contexts", "source": {"kind": "output", "node_id": "slice", "port": "result"},
            "path": ["members"], "mode": "references", "output": {"name": "result", "value_type": contexts},
            "limits": {"max_items": 32, "max_artifacts": 33, "max_bytes": 262144, "timeout_seconds": 120}}
        scatter = {"kind": "scatter", "node_id": "evaluate", "collection": {"kind": "output", "node_id": "candidate_contexts", "port": "result"},
            "item_input": "candidate", "captures": [], "max_members": 32, "max_parallel": 4,
            "body": self.definition["body"], "result_port": "result", "output": {"name": "result", "value_type": results}, "policy": {"kind": "all"}}
        finish = {"kind": "finish", "node_id": "finish", "outputs": [{"port": "result",
            "source": {"kind": "output", "node_id": "evaluate", "port": "result"}}]}
        body["nodes"] = [*body["nodes"][:-1], project, scatter, finish]
        body["outputs"][0]["value_type"] = results
        body["edges"] = [{"source": left["node_id"], "target": right["node_id"], "route": "next"}
                         for left, right in zip(body["nodes"], body["nodes"][1:])]

    def configure(self, runtime, models):
        entry = {"descriptor": "population-method-release.json", "lock": release_lock(self.descriptor)}
        schemas = [{"schema_ref": ref.model_dump(), "path": "population-schema-" + str(index) + ".json"}
            for index, (_, ref) in enumerate(models) if ref.sha256 in {
                self.descriptor["tool"]["inputs"][0]["schema_ref"]["sha256"], self.descriptor["tool"]["outputs"][0]["schema_ref"]["sha256"]}]
        runtime["graphs"][0]["releases"].append(entry)
        runtime["graphs"][0]["schemas"].extend(schemas)
        runtime["graphs"].append({"definition": "population-method-graph.json", "releases": [entry], "schemas": schemas})

    def pin(self, original, definition_reference, plan_sha256):
        method = original["method_graph"]["methods"][0]
        method.update(node_path=["cost"], tool=self.descriptor["tool"]["binding"],
            input_schema=self.descriptor["tool"]["inputs"][0]["schema_ref"],
            output_schema=self.descriptor["tool"]["outputs"][0]["schema_ref"])
        original["method_graph"].update(definition=definition_reference, plan_sha256=plan_sha256, methods=[method])
        original["assembly"]["objectives"] = [original["assembly"]["objectives"][0]]
        original["assembly"]["objectives"][0]["method_ids"] = [method["method_id"]]

    def run(self, run, members, worker_config, call, command, read):
        expected = {PopulationCandidateContext.model_validate_json(json.dumps(read(ref.model_dump(mode="json")))).member.candidate_id for ref in members}
        observed, completions = {}, []
        advance = command("graph.advance", {"run_id": run, "max_transitions": 10})
        for turn in range(64):
            advanced = call(self.runtime_port, "/v1/graph-runs/advance", advance)
            state = call(self.runtime_port, "/v1/runs/" + run)
            if state["status"] == "completed":
                break
            assert state["status"] == "running", state
            if advanced["outcome"]["status"] != "pending":
                assert advanced["outcome"]["status"] != "rejected", advanced
                advance = command("graph.advance", {"run_id": run, "max_transitions": 10})
            if not any(activation["status"] == "queued" for activation in state["activations"]):
                continue
            result = subprocess.run([str(self.python), "-I", "-m", "amphora_evolution_search", "population-worker",
                "--operation", self.operation, "--config", str(worker_config)], env=self.environment, capture_output=True, timeout=1200)
            (self.output / ("population-method-" + str(turn) + ".log")).write_bytes(result.stdout + result.stderr)
            assert result.returncode == 0, "Actual method worker failed; inspect method log"
            receipt = json.loads(result.stdout)
            assert receipt.get("outcome") == "succeeded", receipt
            completion = call(self.runtime_port, f"/v1/runs/{run}/completions/" + receipt["operation_id"])
            assert completion["canonical_result"]
            output = completion["result"]["outcome"]["outputs"][0]["artifact"]
            derivation = call(self.data_port, "/v1/artifacts/" + output["artifact_id"] + "/derivation")
            declaration = derivation["declaration"]
            assert declaration["transformation"]["transformation_id"] == self.descriptor["tool"]["binding"]["capability_id"]
            inputs = [ref for ref in declaration["inputs"] if ref["schema_ref"] == population_step_schema("population-step.candidate-context").model_dump()]
            assert len(inputs) == 1
            context = PopulationCandidateContext.model_validate_json(json.dumps(read(inputs[0])))
            birth = CandidateBirth.model_validate_json(json.dumps(read(context.member.birth.model_dump(mode="json"))))
            value = ObjectiveValue.model_validate_json(json.dumps(read(output)))
            expected_value = math.fsum(g * g for g in birth.genes) if self.operation == "evaluate-squares" else -math.fsum(birth.genes)
            assert value.value == expected_value and context.generation.run_id == run
            assert context.member.candidate_id not in observed
            observed[context.member.candidate_id] = value.value
            reservation = completion["retention_reservation_ids"][0]
            closure = call(self.data_port, "/v1/retention-closures/" + reservation)
            binding = closure["reservation"]["outcome"]["binding"]
            call(self.data_port, "/v1/reservations/confirm", command("artifacts.confirm", {"reservation_id": reservation,
                "intent_id": binding["intent"]["intent_id"], "runtime_receipt_id": receipt["operation_id"]}))
            completions.append(receipt["operation_id"])
        else:
            raise AssertionError("Numerical scatter did not finish within bounded coordinator passes")
        assert set(observed) == expected and len(completions) == 8
        assert state["budget"]["spent"] == 10
        return {"operation": self.operation, "evaluated_members": len(observed), "context_bound_by_derivation": True,
            "exact_values_verified": True, "spent": 10, "run_status": state["status"], "method_plan": "population-primary-method"}
