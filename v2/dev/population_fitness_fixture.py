"""Actual installed synthetic assembly and explicit unavailable fitness."""
import json
import math
import subprocess

from amphora_contracts_core import SchemaRef
from amphora_contracts_population import FitnessManifest,FitnessPage,population_record_schema
from amphora_evolution_search.population_workers.method_plan import payload_schema
from amphora_evolution_search.population_workers.payloads import FittedPrimaryGeneration,PrimarySumPolicy,UnconstrainedSynthetic
from population_method_fixture import release_lock,shape
from verify_retention_closure_installation import write


class FitnessFixture:
    def __init__(self,output,python,scope,environment,ports, *, case="normal", operation="evaluate-squares"):
        self.output,self.python,self.scope,self.environment=output,python,scope,environment
        self.data_port,self.runtime_port=ports;self.case=case;self.operation=operation
        result=subprocess.run([str(python),"-I","-m","amphora_evolution_search","population-describe",
            "--operation","assemble-primary","--image-sha256","f"*64],capture_output=True,timeout=120)
        assert result.returncode==0,"Installed assembly descriptor failed"
        self.descriptor=json.loads(result.stdout)
        write(output/"population-fitness-release.json",self.descriptor)
        self.models=((FittedPrimaryGeneration,SchemaRef.model_validate(self.descriptor["tool"]["outputs"][0]["schema_ref"])),
            (PrimarySumPolicy,payload_schema(PrimarySumPolicy,"population-worker.fitness-policy")),
            (UnconstrainedSynthetic,payload_schema(UnconstrainedSynthetic,"population-worker.synthetic-constraints")),
            (FitnessPage,population_record_schema("population.fitness-page")),(FitnessManifest,population_record_schema("population.fitness-manifest")))
        self.worker={"actor_id":"population-fitness","scope":scope,"token_env":"QUAL_FITNESS_TOKEN"}
        environment["QUAL_FITNESS_TOKEN"]="v"*32

    def decorate(self,definition):
        body=definition["body"]
        fitness={"kind":"invoke","node_id":"assemble","tool":self.descriptor["tool"]["binding"],
            "inputs":[{"port":"parameters","source":{"kind":"output","node_id":"collect","port":"result"}}],"timeout_seconds":3600,"checkpoint":None}
        finish={"kind":"finish","node_id":"finish","outputs":[{"port":"result","source":{"kind":"output","node_id":"assemble","port":"result"}}]}
        body["nodes"]=[*body["nodes"][:-1],fitness,finish]
        body["outputs"][0]["value_type"]=shape(self.descriptor,"outputs")
        body["edges"]=[{"source":a["node_id"],"target":b["node_id"],"route":"next"} for a,b in zip(body["nodes"],body["nodes"][1:])]

    def configure(self,runtime,models):
        runtime["principals"].append({**self.worker,"actions":["claim","renew","complete","read","inspect_receipts"]})
        runtime["graphs"][0]["releases"].append({"descriptor":"population-fitness-release.json","lock":release_lock(self.descriptor)})
        needed={self.descriptor["tool"][direction][0]["schema_ref"]["sha256"] for direction in ("inputs","outputs")}
        present={entry["schema_ref"]["sha256"] for entry in runtime["graphs"][0]["schemas"]}
        runtime["graphs"][0]["schemas"].extend({"schema_ref":ref.model_dump(),"path":"population-schema-"+str(index)+".json"}
            for index,(_,ref) in enumerate(models) if ref.sha256 in needed-present)

    def pin(self,original,publish,context):
        original["assembly"]["tool"]=self.descriptor["tool"]["binding"]
        original["assembly"]["policy"]=publish(PrimarySumPolicy(schema_version="1",profile="primary-dimensionless-sum-v1").model_dump(mode="json"),
            self.models[1][1].model_dump(),[context])
        original["constraints"]=publish(UnconstrainedSynthetic(schema_version="1",profile="unconstrained-synthetic-v1").model_dump(mode="json"),
            self.models[2][1].model_dump(),[context])

    def run(self,run,worker_config,call,command,read, *, stop_after_fitness=False):
        config=json.loads(worker_config.read_bytes());config.update(actor_id=self.worker["actor_id"],lease_seconds=300)
        for name in ("runtime","artifacts"):config[name]["token_env"]="QUAL_FITNESS_TOKEN"
        path=self.output/"population-fitness-worker.json";write(path,config)
        result=subprocess.run([str(self.python),"-I","-m","amphora_evolution_search","population-worker","--operation","assemble-primary",
            "--config",str(path)],env=self.environment,capture_output=True,timeout=1200)
        (self.output/"population-fitness-worker.log").write_bytes(result.stdout+result.stderr)
        assert result.returncode==0,"Actual assembly failed; inspect fitness worker log"
        receipt=json.loads(result.stdout);assert receipt.get("outcome")=="succeeded",receipt
        completion=call(self.runtime_port,f"/v1/runs/{run}/completions/"+receipt["operation_id"])
        root=completion["result"]["outcome"]["outputs"][0]["artifact"]
        fitted=FittedPrimaryGeneration.model_validate_json(json.dumps(read(root)))
        manifest=FitnessManifest.model_validate_json(json.dumps(read(fitted.fitness.model_dump(mode="json"))))
        records=[row for page in manifest.pages for row in FitnessPage.model_validate_json(json.dumps(read(page.artifact.model_dump(mode="json")))).records]
        available=[row for row in records if row.outcome.status=="evaluated"]
        unavailable=[row for row in records if row.outcome.status=="unavailable"]
        expected={"normal":16,"failed-required":15,"conditional-not-taken":0}[self.case]
        assert len(records)==manifest.member_count==16 and len(available)==expected and len(unavailable)==16-expected
        from amphora_contracts_population import MembershipManifest,MembershipPage,CandidateBirth
        pool=MembershipManifest.model_validate_json(json.dumps(read(fitted.pool.model_dump(mode="json"))))
        members=[member for page in pool.pages for member in MembershipPage.model_validate_json(json.dumps(read(page.artifact.model_dump(mode="json")))).members]
        assert pool.role=="selection_pool" and {m.candidate_id for m in members}=={row.candidate_id for row in records}
        by_id={member.candidate_id:member for member in members}
        for record in available:
            birth=CandidateBirth.model_validate_json(json.dumps(read(by_id[record.candidate_id].birth.model_dump(mode="json"))))
            expected_value=math.fsum(gene*gene for gene in birth.genes) if self.operation=="evaluate-squares" else -math.fsum(birth.genes)
            assert record.outcome.objectives[0].value.value==expected_value
            assert record.outcome.objectives[0].quality=="synthetic" and record.outcome.constraint_violation==0.0
        for record in unavailable:
            assert record.outcome.reason_code=="required_method_unavailable" and "objectives" not in record.outcome.model_dump()
        reservation=completion["retention_reservation_ids"][0]
        closure=call(self.data_port,"/v1/retention-closures/"+reservation);binding=closure["reservation"]["outcome"]["binding"]
        call(self.data_port,"/v1/reservations/confirm",command("artifacts.confirm",{"reservation_id":reservation,
            "intent_id":binding["intent"]["intent_id"],"runtime_receipt_id":receipt["operation_id"]}))
        import http.client
        connection=http.client.HTTPConnection("127.0.0.1",self.data_port,timeout=10)
        try:
            connection.request("GET","/v1/retention-closures/"+reservation,headers={"Authorization":"Bearer "+"v"*32})
            response=connection.getresponse();assert response.status==403;response.read()
        finally:connection.close()
        for _ in range(16):
            call(self.runtime_port,"/v1/graph-runs/advance",command("graph.advance",{"run_id":run,"max_transitions":32}))
            state=call(self.runtime_port,"/v1/runs/"+run)
            if state["status"]=="completed" or (stop_after_fitness and any(a["status"]=="queued" for a in state["activations"])):break
        spent=4 if self.case=="conditional-not-taken" else 20
        assert state["status"]==("running" if stop_after_fitness else "completed") and state["budget"]["spent"]==spent,state
        record={"status":"passed","case":self.case,"members":16,"available":len(available),"unavailable":len(unavailable),
            "exact_available_values":True,"initial_selection_pool":True,"retained_artifacts":closure["artifact_count"],
            "run_status":state["status"],"spent":spent,"fitness_retention_grant":False,"provider_calls":0}
        write(self.output/"population-fitness-evidence.json",record)
        return record
