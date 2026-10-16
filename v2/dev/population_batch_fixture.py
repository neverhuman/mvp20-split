"""Actual installed slice loop; bounded two-batch restart proof, not E2.4 matrix."""
import json
from pathlib import Path
import subprocess

from amphora_contracts_population_steps import PopulationMemberSlice,population_step_schema
from verify_retention_closure_installation import ROOT,write


class BatchFixture:
    def __init__(self,method):
        self.method=method
        self.batch=8

    def decorate(self,definition):
        owner=self.method
        write(owner.output/"batch-author-input.json",dict(method=owner.definition,max_population=16,
            batch_size=self.batch,max_parallel=4,image_sha256="f"*64,
            initial=dict(kind="output",node_id="slice_request",port="result"),
            prepared=dict(kind="output",node_id="seed",port="result")))
        result=subprocess.run([str(owner.python),"-I",str(ROOT/"dev/verify_population_batch_compile.py"),
            "author",str(owner.output)],capture_output=True,timeout=120)
        (owner.output/"batch-author.log").write_bytes(result.stdout+result.stderr)
        assert result.returncode==0,"Installed batch author failed; inspect batch-author.log"
        packet=json.loads((owner.output/"batch-author-output.json").read_bytes())
        body=definition["body"]
        kept=[next(node for node in body["nodes"] if node["node_id"]==name) for name in ("seed","slice_request")]
        body["nodes"]=[*kept,packet["loop"],dict(kind="finish",node_id="finish",outputs=[dict(port="result",
            source=dict(kind="output",node_id="batches",port="request"))])]
        body["outputs"][0]["value_type"]=packet["request_shape"]
        body["edges"]=[dict(source=a["node_id"],target=b["node_id"],route="next")
            for a,b in zip(body["nodes"],body["nodes"][1:])]

    def preflight(self,ready,definition,original):
        owner=self.method
        write(owner.output/"batch-preflight-input.json",dict(plan=ready["plan_records"][definition["campaign_id"]],
            expected_plan_sha256=ready["plan_sha256"],specification=original))
        result=subprocess.run([str(owner.python),"-I",str(ROOT/"dev/verify_population_batch_compile.py"),
            "assess",str(owner.output)],capture_output=True,timeout=120)
        (owner.output/"batch-preflight.log").write_bytes(result.stdout+result.stderr)
        assert result.returncode==0,"Installed batch preflight failed; inspect batch-preflight.log"

    def run(self,run,prepared,worker_config,call,command,read,start,stop,environment):
        owner=self.method
        manifest=read(read(prepared)["cohort"])
        expected={row["candidate_id"] for page in manifest["pages"] for row in read(page["artifact"])["members"]}
        seen=set();next_index=0;batches=[];restarted=False
        advance=command("graph.advance",dict(run_id=run,max_transitions=10))
        for turn in range(128):
            advanced=call(owner.runtime_port,"/v1/graph-runs/advance",advance)
            state=call(owner.runtime_port,"/v1/runs/"+run)
            if state["status"]=="completed":break
            assert state["status"]=="running",state
            if advanced["outcome"]["status"]!="pending":
                assert advanced["outcome"]["status"]!="rejected",advanced
                advance=command("graph.advance",dict(run_id=run,max_transitions=10))
            if not any(item["status"]=="queued" for item in state["activations"]):continue
            result=subprocess.run([str(owner.python),"-I","-m","amphora_evolution_search","population-worker",
                "--operation","slice","--config",str(worker_config)],env=environment,capture_output=True,timeout=1200)
            (owner.output/("batch-slice-"+str(turn)+".log")).write_bytes(result.stdout+result.stderr)
            assert result.returncode==0,"Actual batch slice failed; inspect batch-slice log"
            receipt=json.loads(result.stdout)
            assert receipt.get("outcome")=="succeeded",receipt
            completion=call(owner.runtime_port,f"/v1/runs/{run}/completions/"+receipt["operation_id"])
            assert completion["canonical_result"]
            output=completion["result"]["outcome"]["outputs"][0]["artifact"]
            sliced=PopulationMemberSlice.model_validate_json(json.dumps(read(output)))
            assert sliced.prepared.model_dump(mode="json")==prepared and sliced.start_index==next_index
            assert len(sliced.members)==self.batch and sliced.next_index==next_index+self.batch
            identities={read(ref.model_dump(mode="json"))["member"]["candidate_id"] for ref in sliced.members}
            assert len(identities)==self.batch and not (seen&identities)
            seen.update(identities);next_index=sliced.next_index
            reservation=completion["retention_reservation_ids"][0]
            closure=call(owner.data_port,"/v1/retention-closures/"+reservation)
            binding=closure["reservation"]["outcome"]["binding"]
            call(owner.data_port,"/v1/reservations/confirm",command("artifacts.confirm",dict(reservation_id=reservation,
                intent_id=binding["intent"]["intent_id"],runtime_receipt_id=receipt["operation_id"])))
            spent=call(owner.runtime_port,"/v1/runs/"+run)["budget"]["spent"]
            batches.append(owner.run(run,sliced.members,worker_config,call,command,read,
                stop_after_members=True,spent_before=spent,log_prefix="batch-method-"+str(len(batches))))
            if len(batches)==1:
                stop("runtime");stop("data")
                start("data",Path(environment["QUAL_DATA_PYTHON"]),owner.data_port,environment)
                start("runtime",Path(environment["QUAL_RUNTIME_PYTHON"]),owner.runtime_port,environment)
                restarted=True
        else:raise AssertionError("Authored batch loop did not finish in128 coordinator passes")
        assert seen==expected and len(batches)==2 and next_index==16 and restarted
        assert state["budget"]["spent"]==19
        evidence=dict(status="passed",batch_size=8,batches=2,candidates=16,spent=19,
            source_membership_preserved=True,disjoint_contexts=True,both_owners_restarted=True,
            actual_cursor_feedback=True,provider_calls=0,scope="E2.3 authored two-batch primitive; no matrix credit")
        write(owner.output/"population-batch-evidence.json",evidence)
        print("Actual authored two-batch loop completed across both owner restarts",flush=True)
        return evidence
