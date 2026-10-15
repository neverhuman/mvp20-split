"""Bounded static later-wave fixture; not generic graph-loop qualification."""
import copy
import json
import subprocess
from dataclasses import dataclass

from amphora_evolution_search.population_workers.capabilities import PopulationCapability
from amphora_evolution_search.population_workers.payloads import PrimarySuccessorDecision, PreparedPrimarySuccessor
from population_method_fixture import shape
from verify_retention_closure_installation import write


@dataclass(frozen=True)
class FixtureWave:
    generation: int
    prepared_spent: int
    members: int

    @property
    def prefix(self): return "population-successor" if self.generation == 1 else "population-generation"+str(self.generation)

    @property
    def method_spent(self): return self.prepared_spent+2+self.members

    @property
    def fitness_spent(self): return self.method_spent+3

    @property
    def selection_spent(self): return self.fitness_spent+2


def decorate_later_successor(definition, full):
    body = definition["body"]
    nodes = list(body["nodes"][:-1])
    start = next(index for index,node in enumerate(nodes) if node["node_id"] == "successor_request")
    source = nodes[start:] if full else nodes[start:start+2]
    renamed = {node["node_id"]: "second_"+node["node_id"] for node in source}
    def rewrite(value):
        if isinstance(value,list): return [rewrite(item) for item in value]
        if not isinstance(value,dict): return value
        return {key: renamed.get(item,item) if key == "node_id" else rewrite(item) for key,item in value.items()}
    children = [rewrite(copy.deepcopy(node)) for node in source]
    children[0]["inputs"][0]["source"]["node_id"] = "successor_select"
    if full:
        scope = copy.deepcopy(next(item for item in body["inputs"] if item["name"] == "successor_method_scope_path"))
        scope["name"] = "second_method_scope_path"; body["inputs"].append(scope)
        materialize = next(node for node in children if node["node_id"] == "second_successor_collection_request")
        next(field for field in materialize["fields"] if field["name"] == "method_scope_path")["source"]["name"] = "second_method_scope_path"
    nodes.extend(children)
    nodes.append(dict(kind="finish",node_id="finish",outputs=[dict(port="result",
        source=dict(kind="output",node_id=children[-1]["node_id"],port="result"))]))
    body["nodes"] = nodes
    operation = "select-primary" if full else "prepare-successor"
    body["outputs"][0]["value_type"] = shape(PopulationCapability(operation).descriptor("f"*64).model_dump(mode="json"),"outputs")
    body["edges"] = [dict(source=a["node_id"],target=b["node_id"],route="next") for a,b in zip(nodes,nodes[1:])]


def run_later_successor(fixture, run, worker_config, selected, call, command, read):
    for operation in ("prepare-successor-request","prepare-successor"):
        for _ in range(32):
            call(fixture.runtime_port,"/v1/graph-runs/advance",command("graph.advance",dict(run_id=run,max_transitions=32)))
            state=call(fixture.runtime_port,"/v1/runs/"+run)
            if any(item["status"] == "queued" for item in state["activations"]): break
        else: raise AssertionError("Later preparation never became ready")
        result=subprocess.run([str(fixture.python),"-I","-m","amphora_evolution_search","population-worker",
            "--operation",operation,"--config",str(worker_config)],env=fixture.environment,capture_output=True,timeout=1200)
        (fixture.output/("population-later-"+operation+".log")).write_bytes(result.stdout+result.stderr)
        assert result.returncode == 0,"Actual later preparation failed; inspect log"
        receipt=json.loads(result.stdout);assert receipt.get("outcome") == "succeeded",receipt
        completion=call(fixture.runtime_port,f"/v1/runs/{run}/completions/"+receipt["operation_id"])
        reservation=completion["retention_reservation_ids"][0]
        closure=call(fixture.data_port,"/v1/retention-closures/"+reservation)
        binding=closure["reservation"]["outcome"]["binding"]
        call(fixture.data_port,"/v1/reservations/confirm",command("artifacts.confirm",dict(reservation_id=reservation,
            intent_id=binding["intent"]["intent_id"],runtime_receipt_id=receipt["operation_id"])))
    decision=PrimarySuccessorDecision.model_validate_json(json.dumps(read(completion["result"]["outcome"]["outputs"][0]["artifact"])))
    assert decision.checkpoint == selected.checkpoint
    if fixture.generations == 1:
        assert decision.stopped and decision.reason_code == "generation_budget" and decision.successor is None
        for _ in range(16):
            call(fixture.runtime_port,"/v1/graph-runs/advance",command("graph.advance",dict(run_id=run,max_transitions=32)))
            state=call(fixture.runtime_port,"/v1/runs/"+run)
            if state["status"] == "completed": break
        assert state["status"] == "completed" and state["budget"]["spent"] == 49,state
        write(fixture.output/"population-later-stop-evidence.json",dict(status="passed",checkpoint_generation=1,
            stopped=True,reason_code=decision.reason_code,new_births=0,spent=49,retained_artifacts=closure["artifact_count"],provider_calls=0))
    else:
        assert not decision.stopped
        detail=PreparedPrimarySuccessor.model_validate_json(json.dumps(read(decision.successor.model_dump(mode="json"))))
        assert detail.generation.generation == 2 and detail.generation.predecessor == selected.checkpoint
        assert detail.rng.counter == 208
        from population_successor_consumption_fixture import consume_successor
        consume_successor(fixture,run,worker_config,fixture.method_fixture,call,command,read,detail,
            generation=2,prepared_spent=49)
