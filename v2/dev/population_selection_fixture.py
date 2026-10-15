"""Actual installed whole-cohort selection and closed-cut work counters."""
import json
import subprocess
import time

from amphora_contracts_core import SchemaRef
from amphora_contracts_population import (PopulationCheckpoint,PopulationSelectionReceipt,SelectionPage,FitnessManifest,FitnessPage,population_record_schema)
from amphora_contracts_population_steps import SelectPopulationRequest,population_step_schema
from amphora_evolution_search.population_workers.payloads import SelectedPrimaryGeneration
from population_method_fixture import release_lock,shape
from verify_retention_closure_installation import write


class SelectionFixture:
    def __init__(self,output,python,scope,environment,ports, *, case="normal"):
        self.output,self.python,self.scope,self.environment=output,python,scope,environment
        self.data_port,self.runtime_port=ports;self.case=case;self.descriptors={}
        for operation in ("prepare-selection","select-primary"):
            result=subprocess.run([str(python),"-I","-m","amphora_evolution_search","population-describe",
                "--operation",operation,"--image-sha256","f"*64],capture_output=True,timeout=120)
            assert result.returncode==0,"Installed selection descriptor failed"
            descriptor=json.loads(result.stdout);self.descriptors[operation]=descriptor
            write(output/("population-"+operation+"-release.json"),descriptor)
        selected=self.descriptors["select-primary"]
        self.models=((SelectPopulationRequest,population_step_schema("population-step.select")),
            (SelectedPrimaryGeneration,SchemaRef.model_validate(selected["tool"]["outputs"][0]["schema_ref"])),
            (SelectionPage,population_record_schema("population.selection-page")),
            (PopulationSelectionReceipt,population_record_schema("population.selection-receipt")),
            (PopulationCheckpoint,population_record_schema("population.checkpoint")))
        self.worker={"actor_id":"population-selection","scope":scope,"token_env":"QUAL_SELECTION_TOKEN"}
        environment["QUAL_SELECTION_TOKEN"]="s"*32

    def decorate(self,definition):
        body=definition["body"];nodes=list(body["nodes"][:-1]);source="assemble"
        for operation,name in (("prepare-selection","selection_request"),("select-primary","select")):
            descriptor=self.descriptors[operation]
            nodes.append({"kind":"invoke","node_id":name,"tool":descriptor["tool"]["binding"],
                "inputs":[{"port":"parameters","source":{"kind":"output","node_id":source,"port":"result"}}],
                "timeout_seconds":3600,"checkpoint":None})
            source=name
        nodes.append({"kind":"finish","node_id":"finish","outputs":[{"port":"result","source":{"kind":"output","node_id":"select","port":"result"}}]})
        body["nodes"]=nodes;body["outputs"][0]["value_type"]=shape(self.descriptors["select-primary"],"outputs")
        body["edges"]=[{"source":a["node_id"],"target":b["node_id"],"route":"next"} for a,b in zip(nodes,nodes[1:])]

    def configure(self,runtime,models):
        runtime["principals"].append({**self.worker,"actions":["claim","renew","complete","read","inspect_receipts"]})
        for operation,descriptor in self.descriptors.items():
            runtime["graphs"][0]["releases"].append({"descriptor":"population-"+operation+"-release.json","lock":release_lock(descriptor)})
            needed={descriptor["tool"][direction][0]["schema_ref"]["sha256"] for direction in ("inputs","outputs")}
            present={entry["schema_ref"]["sha256"] for entry in runtime["graphs"][0]["schemas"]}
            runtime["graphs"][0]["schemas"].extend({"schema_ref":ref.model_dump(),"path":"population-schema-"+str(index)+".json"}
                for index,(_,ref) in enumerate(models) if ref.sha256 in needed-present)

    def run(self,run,worker_config,call,command,read, *, stop_after_selection=False):
        config=json.loads(worker_config.read_bytes());config.update(actor_id=self.worker["actor_id"],lease_seconds=300)
        for name in ("runtime","artifacts"):config[name]["token_env"]="QUAL_SELECTION_TOKEN"
        path=self.output/"population-selection-worker.json";write(path,config)
        receipt=None
        for operation in ("prepare-selection","select-primary"):
            advance=command("graph.advance",{"run_id":run,"max_transitions":32})
            for _ in range(32):
                moved=call(self.runtime_port,"/v1/graph-runs/advance",advance)
                state=call(self.runtime_port,"/v1/runs/"+run)
                if any(a["status"]=="queued" for a in state["activations"]):break
                assert state["status"]=="running",state
                if moved["outcome"]["status"]!="pending":advance=command("graph.advance",{"run_id":run,"max_transitions":32})
                time.sleep(.1)
            else:raise AssertionError("Selection step did not become ready")
            result=subprocess.run([str(self.python),"-I","-m","amphora_evolution_search","population-worker","--operation",operation,
                "--config",str(path)],env=self.environment,capture_output=True,timeout=1200)
            (self.output/("population-"+operation+"-worker.log")).write_bytes(result.stdout+result.stderr)
            assert result.returncode==0,"Actual selection failed; inspect selection worker log"
            receipt=json.loads(result.stdout);assert receipt.get("outcome")=="succeeded",receipt
            completion=call(self.runtime_port,f"/v1/runs/{run}/completions/"+receipt["operation_id"])
            reservation=completion["retention_reservation_ids"][0]
            closure=call(self.data_port,"/v1/retention-closures/"+reservation);binding=closure["reservation"]["outcome"]["binding"]
            call(self.data_port,"/v1/reservations/confirm",command("artifacts.confirm",{"reservation_id":reservation,
                "intent_id":binding["intent"]["intent_id"],"runtime_receipt_id":receipt["operation_id"]}))
        selected=SelectedPrimaryGeneration.model_validate_json(json.dumps(read(completion["result"]["outcome"]["outputs"][0]["artifact"])))
        checkpoint=PopulationCheckpoint.model_validate_json(json.dumps(read(selected.checkpoint.model_dump(mode="json"))))
        selection=PopulationSelectionReceipt.model_validate_json(json.dumps(read(selected.selection.model_dump(mode="json"))))
        fitness=FitnessManifest.model_validate_json(json.dumps(read(selected.fitness.model_dump(mode="json"))))
        fitness_rows=[row for page in fitness.pages for row in FitnessPage.model_validate_json(json.dumps(read(page.artifact.model_dump(mode="json")))).records]
        rows=[row for page in selection.pages for row in SelectionPage.model_validate_json(json.dumps(read(page.artifact.model_dump(mode="json")))).members]
        expected={row.candidate_id for row in fitness_rows if row.outcome.status=="evaluated"}
        assert selection.member_count==len(rows)==16 and set(selection.selected)==expected
        assert {row.candidate_id for row in rows if row.status=="excluded"}=={row.candidate_id for row in fitness_rows if row.outcome.status=="unavailable"}
        assert selected.stopped==(self.case=="conditional-not-taken" or not stop_after_selection)
        assert selected.stop_reason==("no_feasible_survivors" if self.case=="conditional-not-taken" else None if stop_after_selection else "generation_budget")
        spent=6 if self.case=="conditional-not-taken" else 22
        assert checkpoint.progress.evaluations_issued==checkpoint.progress.evaluations_terminal==16
        assert checkpoint.progress.attempts_issued==spent
        snapshot=call(self.runtime_port,f"/v1/graph-observations/{run}/nodes")
        assert checkpoint.progress.activations_created==snapshot["snapshot"]["node_count"]
        for _ in range(16):
            call(self.runtime_port,"/v1/graph-runs/advance",command("graph.advance",{"run_id":run,"max_transitions":32}))
            state=call(self.runtime_port,"/v1/runs/"+run)
            if state["status"]=="completed" or (stop_after_selection and any(a["status"]=="queued" for a in state["activations"])):break
        assert state["status"]==("running" if stop_after_selection else "completed") and state["budget"]["spent"]==spent,state
        record={"status":"passed","case":self.case,"members":16,"selected":len(expected),"excluded":16-len(expected),
            "attempts_issued":checkpoint.progress.attempts_issued,"activations_created":checkpoint.progress.activations_created,
            "logical_evaluations":16,"retained_artifacts":closure["artifact_count"],"stop_reason":selected.stop_reason,
            "run_status":state["status"],"spent":spent,"provider_calls":0}
        write(self.output/"population-selection-evidence.json",record)
        return record
