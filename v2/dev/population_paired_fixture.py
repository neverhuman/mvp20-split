"""Two named numerical methods on unequal candidate branches, public owners only."""
import copy
import json
import math
import subprocess

from amphora_contracts_population import CandidateBirth
from amphora_contracts_population_steps import PopulationCandidateContext,population_step_schema
from amphora_contracts_search import ObjectiveValue
from population_method_fixture import MethodFixture,release_lock,shape
from verify_retention_closure_installation import write


class PairedMethodFixture(MethodFixture):
    operations=("evaluate-squares","evaluate-negative-sum")

    def __init__(self,output,python,scope,environment,ports,*,case="normal"):
        assert case in {"normal","conditional-not-taken"}
        super().__init__(output,python,scope,environment,ports,"evaluate-squares",case="normal")
        self.case=case
        result=subprocess.run([str(python),"-I","-m","amphora_evolution_search","population-describe",
            "--operation",self.operations[1],"--image-sha256","f"*64],capture_output=True,timeout=120)
        assert result.returncode==0,"Second installed method descriptor failed"
        self.second=json.loads(result.stdout)
        assert shape(self.second,"inputs")==shape(self.descriptor,"inputs")
        assert shape(self.second,"outputs")==shape(self.descriptor,"outputs")
        write(output/"population-second-method-release.json",self.second)
        body=self.definition["body"]
        first=body["nodes"][0]
        second=copy.deepcopy(first)
        second.update(node_id="second",tool=self.second["tool"]["binding"])
        body["outputs"][0]["value_type"]=copy.deepcopy(body["inputs"][0]["value_type"])
        body["nodes"]=[first,{"kind":"branch","node_id":"choose_second",
            "predicate":{"kind":"constant","value":case=="normal"}},second,
            {"kind":"join","node_id":"merge","members":[
                {"member_id":"first","source":{"kind":"output","node_id":"cost","port":"result"},"required":True},
                {"member_id":"second","source":{"kind":"output","node_id":"second","port":"result"},"required":False}],
             "policy":{"kind":"all","skipped":"exclude"},"output":{"name":"result","value_type":{
                 "kind":"collection","item":shape(self.descriptor,"outputs"),"max_items":2,"missing_slots":True}}},
            {"kind":"finish","node_id":"finish","outputs":[{"port":"result","source":{"kind":"input","name":"candidate"}}]}]
        body["edges"]=[{"source":a,"target":b,"route":route} for a,b,route in (
            ("cost","merge","next"),("choose_second","second","true"),
            ("choose_second","merge","false"),("second","merge","next"),("merge","finish","next"))]
        write(output/"population-method-graph.json",self.definition)

    def configure(self,runtime,models):
        super().configure(runtime,models)
        entry={"descriptor":"population-second-method-release.json","lock":release_lock(self.second)}
        runtime["graphs"][0]["releases"].append(entry)
        runtime["graphs"][-1]["releases"].append(entry)

    def pin(self,original,definition_reference,plan_sha256):
        super().pin(original,definition_reference,plan_sha256)
        first=original["method_graph"]["methods"][0]
        first["required"]=True
        second=copy.deepcopy(first)
        second.update(method_id="negative-sum",node_path=["second"],tool=self.second["tool"]["binding"],required=True)
        original["method_graph"]["methods"].append(second)
        original["assembly"]["objectives"][0]["method_ids"].append(second["method_id"])

    def run(self,run,members,worker_config,call,command,read,*,stop_after_members=False,**unused):
        assert stop_after_members
        expected={PopulationCandidateContext.model_validate_json(json.dumps(read(ref.model_dump(mode="json")))).member.candidate_id for ref in members}
        operations=self.operations if self.case=="normal" else self.operations[:1]
        wanted={(candidate,operation) for candidate in expected for operation in operations}
        observed=set()
        for turn in range(128):
            call(self.runtime_port,"/v1/graph-runs/advance",command("graph.advance",{"run_id":run,"max_transitions":32}))
            state=call(self.runtime_port,"/v1/runs/"+run)
            assert state["status"]=="running",state
            if observed==wanted:break
            for operation in operations:
                result=subprocess.run([str(self.python),"-I","-m","amphora_evolution_search","population-worker",
                    "--operation",operation,"--config",str(worker_config)],env=self.environment,capture_output=True,timeout=1200)
                (self.output/("population-paired-"+str(turn)+"-"+operation+".log")).write_bytes(result.stdout+result.stderr)
                assert result.returncode==0,"Paired installed worker failed"
                receipt=json.loads(result.stdout)
                if receipt.get("status")=="no_eligible_work":continue
                assert receipt.get("outcome")=="succeeded",receipt
                completion=call(self.runtime_port,f"/v1/runs/{run}/completions/"+receipt["operation_id"])
                assert completion["canonical_result"]
                artifact=completion["result"]["outcome"]["outputs"][0]["artifact"]
                declaration=call(self.data_port,"/v1/artifacts/"+artifact["artifact_id"]+"/derivation")["declaration"]
                descriptor=self.descriptor if operation==self.operations[0] else self.second
                assert declaration["transformation"]["transformation_id"]==descriptor["tool"]["binding"]["capability_id"]
                contexts=[ref for ref in declaration["inputs"] if ref["schema_ref"]==population_step_schema("population-step.candidate-context").model_dump()]
                assert len(contexts)==1
                context=PopulationCandidateContext.model_validate_json(json.dumps(read(contexts[0])))
                assert context.generation.run_id==run and context.generation.generation==0
                key=(context.member.candidate_id,operation)
                assert key in wanted and key not in observed
                birth=CandidateBirth.model_validate_json(json.dumps(read(context.member.birth.model_dump(mode="json"))))
                value=ObjectiveValue.model_validate_json(json.dumps(read(artifact)))
                exact=math.fsum(g*g for g in birth.genes) if operation==self.operations[0] else -math.fsum(birth.genes)
                assert value.value==exact
                observed.add(key)
                reservation=completion["retention_reservation_ids"][0]
                closure=call(self.data_port,"/v1/retention-closures/"+reservation)
                binding=closure["reservation"]["outcome"]["binding"]
                call(self.data_port,"/v1/reservations/confirm",command("artifacts.confirm",{"reservation_id":reservation,
                    "intent_id":binding["intent"]["intent_id"],"runtime_receipt_id":receipt["operation_id"]}))
        else:raise AssertionError("Paired methods did not settle within bounded passes")
        assert observed==wanted and state["budget"]["spent"]==2+len(wanted)
        record=dict(status="passed",members=len(expected),named_methods=2,evaluated=len(observed),
            skipped=len(expected) if self.case!="normal" else 0,exact_values_verified=True,
            context_bound_by_derivation=True,spent=2+len(wanted),provider_calls=0)
        write(self.output/"population-paired-method-evidence.json",record)
        return record
