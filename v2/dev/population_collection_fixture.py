"""Actual installed collection primitive over one complete16-candidate cohort."""
import json
import subprocess
import time

from amphora_contracts_campaigns import ExecutionPlanV4
from amphora_contracts_population import (EvaluationKeyPage,EvaluationManifest,EvaluationResolutionManifest,
    MethodObservationPage,ObservationManifest,population_record_schema)
from amphora_contracts_population_steps import PopulationCandidateContext
from amphora_evolution_search.population_workers.method_plan import payload_schema
from amphora_evolution_search.population_workers.payloads import (
    CollectedPrimaryGeneration,CollectPrimaryRequest,PopulationReferenceGroup,PrimaryOwnerEvidence)

from population_method_fixture import release_lock,shape
from verify_retention_closure_installation import write


class CollectionFixture:
    def __init__(self,output,python,scope,environment,ports, *, case="normal"):
        self.output,self.python,self.scope,self.environment=output,python,scope,environment
        self.data_port,self.runtime_port=ports
        self.case=case
        result=subprocess.run([str(python),"-I","-m","amphora_evolution_search","population-describe",
            "--operation","collect-primary","--image-sha256","f"*64],capture_output=True,timeout=120)
        assert result.returncode==0,"Installed collector descriptor failed"
        self.descriptor=json.loads(result.stdout)
        write(output/"population-collector-release.json",self.descriptor)
        from amphora_contracts_core import SchemaRef
        self.models=((CollectPrimaryRequest,SchemaRef.model_validate(self.descriptor["tool"]["inputs"][0]["schema_ref"])),
            (CollectedPrimaryGeneration,SchemaRef.model_validate(self.descriptor["tool"]["outputs"][0]["schema_ref"])),
            (ExecutionPlanV4,payload_schema(ExecutionPlanV4,"population-worker.execution-plan")),
            (PrimaryOwnerEvidence,payload_schema(PrimaryOwnerEvidence,"population-worker.owner-evidence")),
            (PopulationReferenceGroup,payload_schema(PopulationReferenceGroup,"population-worker.reference-group")),
            *((model,population_record_schema(name)) for model,name in (
                (EvaluationKeyPage,"population.evaluation-key-page"),(EvaluationManifest,"population.evaluation-manifest"),
                (MethodObservationPage,"population.method-observation-page"),(ObservationManifest,"population.observation-manifest"),
                (EvaluationResolutionManifest,"population.evaluation-resolution"))))
        self.worker={"actor_id":"population-collector","scope":scope,"token_env":"QUAL_COLLECTOR_TOKEN"}
        environment["QUAL_COLLECTOR_TOKEN"]="z"*32

    def decorate(self,definition):
        body=definition["body"]
        scatter=next(node for node in body["nodes"] if node["node_id"]=="evaluate")
        scatter["policy"]={"kind":"partial","minimum":0,"close":"all_terminal","deadline_seconds":None}
        scatter["output"]["value_type"]["missing_slots"]=True
        plan_shape={"kind":"artifact","schema_ref":self.models[2][1].model_dump(),"representation":"population-plan-v1","unit":"1","media_type":"application/json"}
        body["inputs"].extend({"name":name,"value_type":plan_shape} for name in ("execution_plan","method_plan"))
        body["inputs"].append({"name":"method_scope_path","value_type":{"kind":"collection","item":{"kind":"scalar","scalar":"string","unit":"1"},"max_items":16,"missing_slots":False}})
        materialize={"kind":"artifact_materialize","node_id":"collection_request","fields":[
            {"name":"schema_version","mode":"inline","source":{"kind":"string","value":"1"}},
            {"name":"prepared","mode":"references","source":{"kind":"output","node_id":"seed","port":"result"}},
            *({"name":name,"mode":"references","source":{"kind":"input","name":name}} for name in ("execution_plan","method_plan")),
            {"name":"method_scope_path","mode":"inline","source":{"kind":"input","name":"method_scope_path"}}],
            "output":{"name":"result","value_type":shape(self.descriptor,"inputs")},
            "limits":{"max_items":32,"max_artifacts":8,"max_bytes":262144,"timeout_seconds":120}}
        collector={"kind":"invoke","node_id":"collect","tool":self.descriptor["tool"]["binding"],
            "inputs":[{"port":"parameters","source":{"kind":"output","node_id":"collection_request","port":"result"}}],
            "timeout_seconds":3600,"checkpoint":None}
        finish={"kind":"finish","node_id":"finish","outputs":[{"port":"result","source":{"kind":"output","node_id":"collect","port":"result"}}]}
        body["nodes"]=[*body["nodes"][:-1],materialize,collector,finish]
        body["outputs"][0]["value_type"]=shape(self.descriptor,"outputs")
        body["edges"]=[{"source":a["node_id"],"target":b["node_id"],"route":"next"} for a,b in zip(body["nodes"],body["nodes"][1:])]

    def configure(self,runtime,models):
        runtime["principals"].append({**self.worker,"actions":["claim","renew","complete","read","inspect_receipts"]})
        runtime["graphs"][0]["releases"].append({"descriptor":"population-collector-release.json","lock":release_lock(self.descriptor)})
        needed={self.descriptor["tool"][direction][0]["schema_ref"]["sha256"] for direction in ("inputs","outputs")}
        needed.add(self.models[2][1].sha256)
        runtime["graphs"][0]["schemas"].extend({"schema_ref":ref.model_dump(),"path":"population-schema-"+str(index)+".json"}
            for index,(_,ref) in enumerate(models) if ref.sha256 in needed)

    def inputs(self,ready,publish):
        records=ready["plan_records"]
        execution=records[next(name for name in records if name!="population-primary-method")]
        method=records["population-primary-method"]
        schema=self.models[2][1].model_dump()
        return [*({"port":name,"value":{"kind":"artifact","representation":"population-plan-v1","unit":"1",
            "artifact":publish(record,schema)}} for name,record in (("execution_plan",execution),("method_plan",method))),
            {"port":"method_scope_path","value":{"kind":"collection","items":[{"kind":"string","value":"evaluate"}]}}]

    def run(self,run,members,worker_config,call,command,read, *, stop_after_collection=False):
        advance=command("graph.advance",{"run_id":run,"max_transitions":32})
        for _ in range(32):
            receipt=call(self.runtime_port,"/v1/graph-runs/advance",advance)
            state=call(self.runtime_port,"/v1/runs/"+run)
            if any(a["status"]=="queued" for a in state["activations"]):break
            assert state["status"]=="running",state
            if receipt["outcome"]["status"]!="pending":advance=command("graph.advance",{"run_id":run,"max_transitions":32})
            time.sleep(.1)
        else:raise AssertionError("Collector did not become ready")
        config=json.loads(worker_config.read_bytes());config.update(actor_id=self.worker["actor_id"],lease_seconds=300)
        for name in ("runtime","artifacts"):config[name]["token_env"]="QUAL_COLLECTOR_TOKEN"
        path=self.output/"population-collector-worker.json";write(path,config)
        result=subprocess.run([str(self.python),"-I","-m","amphora_evolution_search","population-worker","--operation","collect-primary",
            "--config",str(path)],env=self.environment,capture_output=True,timeout=1200)
        (self.output/"population-collector-worker.log").write_bytes(result.stdout+result.stderr)
        assert result.returncode==0,"Actual collector failed; inspect collector worker log"
        receipt=json.loads(result.stdout);assert receipt.get("outcome")=="succeeded",receipt
        completion=call(self.runtime_port,f"/v1/runs/{run}/completions/"+receipt["operation_id"])
        root=completion["result"]["outcome"]["outputs"][0]["artifact"]
        collected=CollectedPrimaryGeneration.model_validate_json(json.dumps(read(root)))
        evaluations=EvaluationManifest.model_validate_json(json.dumps(read(collected.evaluations.model_dump(mode="json"))))
        observations=ObservationManifest.model_validate_json(json.dumps(read(collected.observations.model_dump(mode="json"))))
        rows=[row for page in observations.pages for row in MethodObservationPage.model_validate_json(json.dumps(read(page.artifact.model_dump(mode="json")))).records]
        expected={PopulationCandidateContext.model_validate_json(json.dumps(read(ref.model_dump(mode="json")))).member.candidate_id for ref in members}
        assert evaluations.evaluation_count==observations.terminal_count==len(expected)==16
        assert {row.key.candidate_id for row in rows}==expected
        statuses={status:sum(row.outcome.status==status for row in rows) for status in ("evaluated","failed","inapplicable")}
        expected_statuses={"normal":dict(evaluated=16,failed=0,inapplicable=0),
            "failed-required":dict(evaluated=15,failed=1,inapplicable=0),
            "conditional-not-taken":dict(evaluated=0,failed=0,inapplicable=16)}
        assert statuses==expected_statuses[self.case],statuses
        for row in rows:
            if row.outcome.status!="evaluated":continue
            producer=call(self.runtime_port,f"/v1/runs/{run}/completions/{row.outcome.producer.completion_id}/producer")
            context=PopulationCandidateContext.model_validate_json(json.dumps(read(producer["invocation"]["inputs"][0]["artifact"])))
            assert context.member.candidate_id==row.key.candidate_id
        reservation=completion["retention_reservation_ids"][0]
        closure=call(self.data_port,"/v1/retention-closures/"+reservation);binding=closure["reservation"]["outcome"]["binding"]
        call(self.data_port,"/v1/reservations/confirm",command("artifacts.confirm",{"reservation_id":reservation,
            "intent_id":binding["intent"]["intent_id"],"runtime_receipt_id":receipt["operation_id"]}))
        import http.client
        connection=http.client.HTTPConnection("127.0.0.1",self.data_port,timeout=10)
        try:
            connection.request("GET","/v1/retention-closures/"+reservation,headers={"Authorization":"Bearer "+"z"*32})
            response=connection.getresponse();assert response.status==403;response.read()
        finally:connection.close()
        for _ in range(16):
            call(self.runtime_port,"/v1/graph-runs/advance",command("graph.advance",{"run_id":run,"max_transitions":32}))
            state=call(self.runtime_port,"/v1/runs/"+run)
            if state["status"]=="completed" or (stop_after_collection and any(a["status"]=="queued" for a in state["activations"])):break
        spent=3 if self.case=="conditional-not-taken" else 19
        assert state["status"]==("running" if stop_after_collection else "completed") and state["budget"]["spent"]==spent,state
        record={"status":"passed","members":16,"evaluation_keys":16,"terminal_observations":16,
            "candidate_bound_by_runtime_and_data":True,"retained_artifacts":closure["artifact_count"],
            "run_status":state["status"],"spent":spent,"case":self.case,"outcomes":statuses,"collector_retention_grant":False,"provider_calls":0}
        write(self.output/"population-collection-evidence.json",record)
        return record
