"""Actual initial checkpoint to declared generation1 preparation or explicit stop."""
import json
import subprocess
import time

from amphora_contracts_core import SchemaRef
from amphora_contracts_population import (BirthManifest,BirthPage,MembershipManifest,MembershipPage,EvaluationDeclarationManifest,population_record_schema)
from amphora_contracts_population_steps import ProposePopulationSuccessorRequest,PreparedPopulationGeneration,population_step_schema
from amphora_evolution_search.population_workers.method_plan import payload_schema
from amphora_evolution_search.population_workers.payloads import PrimarySuccessorDecision,PreparedPrimarySuccessor
from population_method_fixture import release_lock,shape
from verify_retention_closure_installation import write


class SuccessorFixture:
    def __init__(self,output,python,scope,environment,ports, *, case="normal",tight=False):
        self.output,self.python,self.scope,self.environment=output,python,scope,environment
        self.data_port,self.runtime_port=ports;self.case=case;self.tight=tight;self.descriptors={}
        for operation in ("prepare-successor-request","prepare-successor"):
            result=subprocess.run([str(python),"-I","-m","amphora_evolution_search","population-describe",
                "--operation",operation,"--image-sha256","f"*64],capture_output=True,timeout=120)
            assert result.returncode==0,"Installed successor descriptor failed"
            descriptor=json.loads(result.stdout);self.descriptors[operation]=descriptor
            write(output/("population-"+operation+"-release.json"),descriptor)
        self.models=((ProposePopulationSuccessorRequest,population_step_schema("population-step.successor")),
            (PrimarySuccessorDecision,SchemaRef.model_validate(self.descriptors["prepare-successor"]["tool"]["outputs"][0]["schema_ref"])),
            (PreparedPrimarySuccessor,payload_schema(PreparedPrimarySuccessor,"population-worker.prepared-successor")))
        self.worker={"actor_id":"population-successor","scope":scope,"token_env":"QUAL_SUCCESSOR_TOKEN"}
        environment["QUAL_SUCCESSOR_TOKEN"]="u"*32

    def decorate(self,definition):
        body=definition["body"];nodes=list(body["nodes"][:-1]);source="select"
        for operation,name in (("prepare-successor-request","successor_request"),("prepare-successor","prepare_successor")):
            descriptor=self.descriptors[operation]
            nodes.append({"kind":"invoke","node_id":name,"tool":descriptor["tool"]["binding"],
                "inputs":[{"port":"parameters","source":{"kind":"output","node_id":source,"port":"result"}}],"timeout_seconds":3600,"checkpoint":None})
            source=name
        nodes.append({"kind":"finish","node_id":"finish","outputs":[{"port":"result","source":{"kind":"output","node_id":source,"port":"result"}}]})
        body["nodes"]=nodes;body["outputs"][0]["value_type"]=shape(self.descriptors["prepare-successor"],"outputs")
        body["edges"]=[{"source":a["node_id"],"target":b["node_id"],"route":"next"} for a,b in zip(nodes,nodes[1:])]

    def configure(self,runtime,models):
        runtime["principals"].append({**self.worker,"actions":["claim","renew","complete","read","inspect_receipts"]})
        for operation,descriptor in self.descriptors.items():
            runtime["graphs"][0]["releases"].append({"descriptor":"population-"+operation+"-release.json","lock":release_lock(descriptor)})
            needed={descriptor["tool"][direction][0]["schema_ref"]["sha256"] for direction in ("inputs","outputs")}
            present={entry["schema_ref"]["sha256"] for entry in runtime["graphs"][0]["schemas"]}
            runtime["graphs"][0]["schemas"].extend({"schema_ref":ref.model_dump(),"path":"population-schema-"+str(index)+".json"}
                for index,(_,ref) in enumerate(models) if ref.sha256 in needed-present)

    def run(self,run,worker_config,call,command,read):
        config=json.loads(worker_config.read_bytes());config.update(actor_id=self.worker["actor_id"],lease_seconds=300)
        for name in ("runtime","artifacts"):config[name]["token_env"]="QUAL_SUCCESSOR_TOKEN"
        path=self.output/"population-successor-worker.json";write(path,config)
        for operation in ("prepare-successor-request","prepare-successor"):
            advance=command("graph.advance",{"run_id":run,"max_transitions":32})
            for _ in range(32):
                moved=call(self.runtime_port,"/v1/graph-runs/advance",advance)
                state=call(self.runtime_port,"/v1/runs/"+run)
                if any(a["status"]=="queued" for a in state["activations"]):break
                assert state["status"]=="running",state
                if moved["outcome"]["status"]!="pending":advance=command("graph.advance",{"run_id":run,"max_transitions":32})
                time.sleep(.1)
            else:raise AssertionError("Successor step did not become ready")
            result=subprocess.run([str(self.python),"-I","-m","amphora_evolution_search","population-worker","--operation",operation,
                "--config",str(path)],env=self.environment,capture_output=True,timeout=1200)
            (self.output/("population-"+operation+"-worker.log")).write_bytes(result.stdout+result.stderr)
            assert result.returncode==0,"Actual successor failed; inspect successor worker log"
            receipt=json.loads(result.stdout);assert receipt.get("outcome")=="succeeded",receipt
            completion=call(self.runtime_port,f"/v1/runs/{run}/completions/"+receipt["operation_id"])
            reservation=completion["retention_reservation_ids"][0]
            closure=call(self.data_port,"/v1/retention-closures/"+reservation);binding=closure["reservation"]["outcome"]["binding"]
            call(self.data_port,"/v1/reservations/confirm",command("artifacts.confirm",{"reservation_id":reservation,
                "intent_id":binding["intent"]["intent_id"],"runtime_receipt_id":receipt["operation_id"]}))
        decision=PrimarySuccessorDecision.model_validate_json(json.dumps(read(completion["result"]["outcome"]["outputs"][0]["artifact"])))
        proposed=0;pool_count=0;rng=None
        if self.case=="conditional-not-taken" or self.tight:
            assert decision.stopped and decision.successor is None
            assert decision.reason_code==("no_feasible_survivors" if self.case=="conditional-not-taken" else "attempt_budget")
        else:
            assert not decision.stopped and decision.successor is not None
            detail=PreparedPrimarySuccessor.model_validate_json(json.dumps(read(decision.successor.model_dump(mode="json"))))
            prepared=PreparedPopulationGeneration.model_validate_json(json.dumps(read(detail.prepared.model_dump(mode="json"))))
            births=BirthManifest.model_validate_json(json.dumps(read(prepared.births.model_dump(mode="json"))))
            rows=[row for page in births.pages for row in BirthPage.model_validate_json(json.dumps(read(page.artifact.model_dump(mode="json")))).records]
            cohort=MembershipManifest.model_validate_json(json.dumps(read(prepared.cohort.model_dump(mode="json"))))
            pool=MembershipManifest.model_validate_json(json.dumps(read(detail.pool.model_dump(mode="json"))))
            declarations=EvaluationDeclarationManifest.model_validate_json(json.dumps(read(prepared.declarations.model_dump(mode="json"))))
            proposed=sum(row.disposition=="proposed" for row in rows);pool_count=pool.member_count;rng=detail.rng.counter
            parents=15 if self.case=="failed-required" else 16
            assert prepared.generation.generation==1 and prepared.generation.predecessor==decision.checkpoint
            assert births.birth_count==len(rows)==16 and cohort.member_count==proposed
            assert pool.member_count==parents+proposed and declarations.slot_count==detail.evaluations_planned==proposed
            assert rng==16*(1+3+3) and detail.method_attempt_capacity>0
        for _ in range(16):
            call(self.runtime_port,"/v1/graph-runs/advance",command("graph.advance",{"run_id":run,"max_transitions":32}))
            state=call(self.runtime_port,"/v1/runs/"+run)
            if state["status"]=="completed":break
        spent=8 if self.case=="conditional-not-taken" else 24
        assert state["status"]=="completed" and state["budget"]["spent"]==spent,state
        record={"status":"passed","case":self.case,"tight_budget":self.tight,"stopped":decision.stopped,"reason_code":decision.reason_code,
            "birth_slots":0 if decision.stopped else 16,"proposed":proposed,"pool_members":pool_count,"rng_counter":rng,
            "retained_artifacts":closure["artifact_count"],"run_status":state["status"],"spent":spent,
            "future_evaluation_keys_invented":False,"future_scientific_dispatch":False,"provider_calls":0}
        write(self.output/"population-successor-evidence.json",record)
        return record
