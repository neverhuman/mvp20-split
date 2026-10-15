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
    def __init__(self, output, python, scope, environment, ports, operation, *, case="normal"):
        self.output, self.python, self.scope, self.environment = output, python, scope, environment
        self.data_port, self.runtime_port = ports
        self.operation = operation
        self.case = case
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
        if case == "conditional-not-taken":
            body=self.definition["body"]
            objective_shape=body["outputs"][0]["value_type"]
            body["outputs"][0]["value_type"]=body["inputs"][0]["value_type"]
            cost=body["nodes"][0]
            body["nodes"]=[{"kind":"branch","node_id":"choose","predicate":{"kind":"constant","value":False}},cost,
                {"kind":"join","node_id":"merge","members":[{"member_id":"method","source":{"kind":"output","node_id":"cost","port":"result"},"required":False}],
                    "policy":{"kind":"all","skipped":"exclude"},"output":{"name":"result","value_type":{"kind":"collection","item":objective_shape,"max_items":1,"missing_slots":True}}},
                {"kind":"finish","node_id":"finish","outputs":[{"port":"result","source":{"kind":"input","name":"candidate"}}]}]
            body["edges"]=[{"source":"choose","target":"cost","route":"true"},{"source":"choose","target":"merge","route":"false"},
                {"source":"cost","target":"merge","route":"next"},{"source":"merge","target":"finish","route":"next"}]
        (output / "population-method-graph.json").write_text(json.dumps(self.definition), encoding="utf-8")

    def decorate(self, definition):
        body = definition["body"]
        contexts = {"kind": "collection", "item": shape(self.descriptor, "inputs"), "max_items": 32, "missing_slots": False}
        results = {"kind": "collection", "item": self.definition["body"]["outputs"][0]["value_type"], "max_items": 32, "missing_slots": False}
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

    def run(self, run, members, worker_config, call, command, read, *, stop_after_members=False):
        expected = {PopulationCandidateContext.model_validate_json(json.dumps(read(ref.model_dump(mode="json")))).member.candidate_id for ref in members}
        observed, completions = {}, []
        if self.case == "conditional-not-taken":
            return {"operation":self.operation,"evaluated_members":0,"skipped_members":len(expected),"spent":2,
                "run_status":"running","method_plan":"population-primary-method"}
        failed_members=0
        advance = command("graph.advance", {"run_id": run, "max_transitions": 10})
        for turn in range(64):
            advanced = call(self.runtime_port, "/v1/graph-runs/advance", advance)
            state = call(self.runtime_port, "/v1/runs/" + run)
            if stop_after_members and set(observed) == expected:
                break
            if state["status"] == "completed":
                break
            assert state["status"] == "running", state
            if advanced["outcome"]["status"] != "pending":
                assert advanced["outcome"]["status"] != "rejected", advanced
                advance = command("graph.advance", {"run_id": run, "max_transitions": 10})
            if not any(activation["status"] == "queued" for activation in state["activations"]):
                continue
            if self.case == "failed-required" and not observed:
                script = """import json,sys,uuid
from pathlib import Path
from amphora_tool_protocol import WorkerConfig,WorkerIdentity,RuntimeClient,ToolAttemptContext
from amphora_contracts_tools import ToolBinding,Completion
from amphora_contracts_runtime import CompleteInvocation
config=WorkerConfig.model_validate_json(Path(sys.argv[1]).read_bytes())
binding=ToolBinding.model_validate(json.loads(Path(sys.argv[2]).read_bytes())["tool"]["binding"])
client=RuntimeClient(config.runtime.transport(),WorkerIdentity(config.actor_id,config.scope))
claimed=client.claim(config.run_id,binding,"failure-claim-"+uuid.uuid4().hex,lease_seconds=60)
assert claimed.outcome.status=="claimed"
attempt=ToolAttemptContext(client,claimed.outcome,60);attempt.refresh();inv=attempt.invocation
completion=Completion.model_validate_json(json.dumps(dict(schema_version="1",invocation_id=inv.invocation_id,
 attempt_id=inv.attempt_id,fence=inv.fence,outcome=dict(status="failed",reason_code="fixture_required_failure",retryable=False))))
receipt=client.complete(CompleteInvocation(run_id=config.run_id,completion=completion),"failure-complete-"+inv.attempt_id,guard=attempt.check)
print(json.dumps(dict(status="completion_accepted",outcome="failed",operation_id=receipt.outcome.binding.operation_id)))
"""
                result=subprocess.run([str(self.python),"-I","-c",script,str(worker_config),str(self.output/"population-method-release.json")],
                    env=self.environment,capture_output=True,timeout=120)
            else:
                result = subprocess.run([str(self.python), "-I", "-m", "amphora_evolution_search", "population-worker",
                    "--operation", self.operation, "--config", str(worker_config)], env=self.environment, capture_output=True, timeout=1200)
            (self.output / ("population-method-" + str(turn) + ".log")).write_bytes(result.stdout + result.stderr)
            assert result.returncode == 0, "Actual method worker failed; inspect method log"
            receipt = json.loads(result.stdout)
            assert receipt.get("outcome") in {"succeeded","failed"}, receipt
            completion = call(self.runtime_port, f"/v1/runs/{run}/completions/" + receipt["operation_id"])
            if receipt["outcome"]=="failed":
                assert self.case=="failed-required" and completion["result"]["outcome"]["status"]=="failed"
                inputs=call(self.runtime_port,f"/v1/graph-observations/{run}/nodes/{completion['activation_id']}/inputs")
                context=PopulationCandidateContext.model_validate_json(json.dumps(read(inputs["invocation"]["inputs"][0]["artifact"])))
                assert context.member.candidate_id not in observed
                observed[context.member.candidate_id]=None;failed_members+=1;completions.append(receipt["operation_id"])
                continue
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
        assert set(observed) == expected and len(completions) == len(expected)
        assert state["budget"]["spent"] == 2 + len(expected)
        return {"operation": self.operation, "evaluated_members": len(observed)-failed_members, "failed_members": failed_members, "context_bound_by_derivation": True,
            "exact_values_verified": True, "spent": 2 + len(expected), "run_status": state["status"], "method_plan": "population-primary-method"}
