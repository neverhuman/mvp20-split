"""Actual transform -> accepted derivation, including owner restart and rejection."""
import hashlib
import http.client
import json
import subprocess
import time
from pathlib import Path

from amphora_contracts_population import MaterialState,ProcessDerivation,population_record_schema
from amphora_process_mapping.capability import ProcessCapability,SCHEMAS
from amphora_process_mapping.payloads import (DerivedMaterialBatch,MaterialCollection,
    ProposedProcessTransform,payload_schema)
from process_mapping_fixture import release_lock
from verify_retention_closure_installation import ROOT,write


def verify(output,python,ports,environment,scope,call,command,start,stop,*,case="normal"):
    data_port,runtime_port=ports
    descriptors={}
    for operation in ("transform-materials","derive-process"):
        result=subprocess.run([str(python),"-I","-m","amphora_process_mapping","describe","--operation",operation,
            "--image-sha256","f"*64],capture_output=True,timeout=120)
        assert result.returncode==0,"Installed process descriptor failed"
        descriptor=json.loads(result.stdout)
        assert descriptor==ProcessCapability(operation).descriptor("f"*64).model_dump(mode="json")
        descriptors[operation]=descriptor
        write(output/(operation+"-release.json"),descriptor)
    transform,derive=(descriptors[name] for name in ("transform-materials","derive-process"))
    schema={"type":"object","properties":{"case":{"enum":["normal","missing-required","cross-context"]}},
        "required":["case"],"additionalProperties":False}
    raw=(json.dumps(schema,sort_keys=True,separators=(",",":"))+"\n").encode()
    fixture_ref=dict(schema_id="fixture.process-transform-source",version="1",sha256=hashlib.sha256(raw).hexdigest())
    (output/"process-source-schema.json").write_bytes(raw)
    source=json.loads(json.dumps(transform))
    source["tool"]["binding"]["capability_id"]="fixture.process-transform-source"
    source["tool"]["purpose"]="Admitted test-only typed precursors; not a scientific source."
    source["tool"]["inputs"][0].update(schema_ref=fixture_ref,representation="fixture-process-source-v1")
    source["tool"]["outputs"][0]={**transform["tool"]["inputs"][0],"name":"result"}
    write(output/"process-source-release.json",source)
    data=json.loads((output/"data.json").read_bytes())
    schemas=[]
    extra=(("state",(MaterialState,"population.material-state")),("derivation",(ProcessDerivation,"population.process-derivation")))
    for name,(model,schema_id) in (*SCHEMAS.items(),*extra):
        raw=payload_schema(model,schema_id)
        ref=dict(schema_id=schema_id,version="1",sha256=hashlib.sha256(raw).hexdigest())
        if schema_id.startswith("population."):assert ref==population_record_schema(schema_id).model_dump()
        filename="process-"+name+"-schema.json";(output/filename).write_bytes(raw)
        data["profiles"].append(dict(media_type="application/json",**ref,schema_path=filename))
        schemas.append(dict(schema_ref=ref,path=filename))
    data["profiles"].append(dict(media_type="application/json",**fixture_ref,schema_path="process-source-schema.json"))
    principals=[]
    for actor,token in (("transform-source","s"*32),("process-transform","t"*32),("process-derive","d"*32)):
        token_env="QUAL_"+actor.replace("-","_").upper()+"_TOKEN";environment[token_env]=token
        principal=dict(actor_id=actor,scope=scope,token_env=token_env)
        data["principals"].append(dict(**principal,actions=["read","upload","finalize"]))
        principals.append(dict(**principal,actions=["claim","renew","complete","read",
            *(["inspect_receipts"] if actor=="process-derive" else [])]))
    write(output/"data.json",data)
    def shape(port):return dict(kind="artifact",schema_ref=port["schema_ref"],representation=port["representation"],unit="1",media_type="application/json")
    def invoke(name,descriptor,origin):return dict(kind="invoke",node_id=name,tool=descriptor["tool"]["binding"],
        inputs=[dict(port="parameters",source=origin)],timeout_seconds=3600,checkpoint=None)
    nodes=[invoke("source",source,dict(kind="input",name="parameters")),
        invoke("transform",transform,dict(kind="output",node_id="source",port="result")),
        dict(kind="artifact_materialize",node_id="derive_request",fields=[
            dict(name="schema_version",mode="inline",source=dict(kind="string",value="1")),
            dict(name="profile",mode="inline",source=dict(kind="string",value="synthetic-derive-process-v1")),
            dict(name="result",mode="references",source=dict(kind="output",node_id="transform",port="result"))],
            output=dict(name="result",value_type=shape(derive["tool"]["inputs"][0])),
            limits=dict(max_items=8,max_artifacts=8,max_bytes=262144,timeout_seconds=120)),
        invoke("derive",derive,dict(kind="output",node_id="derive_request",port="result")),
        dict(kind="finish",node_id="finish",outputs=[dict(port="result",source=dict(kind="output",node_id="derive",port="result"))])]
    definition=dict(schema_version="4",profile="deterministic-v3",campaign_id="process-transform-fixture",revision=1,
        scope=scope,context=[],body=dict(inputs=[dict(name="parameters",value_type=shape(source["tool"]["inputs"][0]))],
        outputs=[dict(name="result",value_type=shape(derive["tool"]["outputs"][0]))],nodes=nodes,
        edges=[dict(source=a["node_id"],target=b["node_id"],route="next") for a,b in zip(nodes,nodes[1:])]))
    write(output/"process-transform-graph.json",definition)
    runtime=json.loads((output/"runtime.json").read_bytes())
    environment["QUAL_PROCESS_CURSOR_KEY"]="k"*64
    runtime["inspection"]=dict(cursor_key_env="QUAL_PROCESS_CURSOR_KEY")
    runtime["principals"][0]["actions"].append("inspect_receipts")
    runtime["principals"].extend(principals)
    runtime["bindings"]=dict(endpoint=f"http://127.0.0.1:{data_port}",token_env="QUAL_TOKEN")
    releases=(("process-source-release.json",source),("transform-materials-release.json",transform),("derive-process-release.json",derive))
    runtime["graphs"]=[dict(definition="process-transform-graph.json",releases=[dict(descriptor=name,lock=release_lock(desc))
        for name,desc in releases],schemas=[*schemas,dict(schema_ref=fixture_ref,path="process-source-schema.json")])]
    write(output/"runtime.json",runtime)
    stop("runtime");stop("data")
    start("data",Path(environment["QUAL_DATA_PYTHON"]),data_port,environment)
    ready=start("runtime",Path(environment["QUAL_RUNTIME_PYTHON"]),runtime_port,environment)
    raw=json.dumps(dict(case=case),sort_keys=True,separators=(",",":" )).encode()
    begin=call(data_port,"/v1/uploads",command("artifacts.begin_upload",dict(content=dict(sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw),media_type="application/json",schema_ref=fixture_ref))))
    connection=http.client.HTTPConnection("127.0.0.1",data_port,timeout=20)
    try:
        connection.request("PUT","/v1/uploads/"+begin["upload_id"]+"/content",raw,headers={"Authorization":"Bearer "+"q"*32})
        response=connection.getresponse();assert response.status==200;response.read()
    finally:connection.close()
    artifact=call(data_port,"/v1/artifacts/finalize",command("artifacts.finalize",dict(upload_id=begin["upload_id"],content=begin["content"])))["artifact"]
    admission=call(runtime_port,"/v1/graph-runs",command("graph.admit",dict(plan_sha256=ready["plan_sha256"],
        inputs=[dict(port="parameters",value=dict(kind="artifact",artifact=artifact,representation="fixture-process-source-v1",unit="1"))],budget=dict(limit=3))))
    run=admission["outcome"]["committed"]["object_id"]
    def config(actor):
        token_env="QUAL_"+actor.replace("-","_").upper()+"_TOKEN";path=output/(actor+"-worker.json")
        write(path,dict(actor_id=actor,scope=scope,run_id=run,image_sha256="f"*64,lease_seconds=60,
            runtime=dict(endpoint=f"http://127.0.0.1:{runtime_port}",token_env=token_env),
            artifacts=dict(endpoint=f"http://127.0.0.1:{data_port}",token_env=token_env)))
        return path
    def execute(args,label):
        result=subprocess.run([str(python),"-I",*map(str,args)],env=environment,capture_output=True,timeout=1200)
        (output/(label+".log")).write_bytes(result.stdout+result.stderr)
        assert result.returncode==0,"Actual process worker failed; inspect "+label+".log"
        receipt=json.loads(result.stdout)
        assert receipt.get("status")=="completion_accepted",receipt
        completion=call(runtime_port,f"/v1/runs/{run}/completions/"+receipt["operation_id"])
        write(output/(label+"-completion.json"),completion)
        assert completion["canonical_result"]
        return receipt,completion
    def confirm(receipt,completion):
        reservation=completion["retention_reservation_ids"][0]
        closure=call(data_port,"/v1/retention-closures/"+reservation)
        binding=closure["reservation"]["outcome"]["binding"]
        call(data_port,"/v1/reservations/confirm",command("artifacts.confirm",dict(reservation_id=reservation,
            intent_id=binding["intent"]["intent_id"],runtime_receipt_id=receipt["operation_id"])))
        return closure
    def ready_step():
        advance=command("graph.advance",dict(run_id=run,max_transitions=32))
        for _ in range(32):
            moved=call(runtime_port,"/v1/graph-runs/advance",advance)
            snapshot=call(runtime_port,"/v1/runs/"+run)
            if any(activation["status"]=="queued" for activation in snapshot["activations"]):return
            assert snapshot["status"]=="running",snapshot
            if moved["outcome"]["status"]!="pending":advance=command("graph.advance",dict(run_id=run,max_transitions=32))
            time.sleep(.1)
        raise AssertionError("Process step did not become ready within bounded coordinator passes")
    receipt,completion=execute([ROOT/"dev/process_transform_bootstrap.py",config("transform-source"),
        output/"process-source-release.json",output/"transform-materials-release.json"],"process-source")
    assert receipt["outcome"]=="succeeded";confirm(receipt,completion)
    ready_step()
    transformed,transform_completion=execute(["-m","amphora_process_mapping","worker","--operation","transform-materials",
        "--config",config("process-transform")],"process-transform")
    failed=case!="normal"
    assert transformed["outcome"]==("failed" if failed else "succeeded")
    retained=0
    if failed:
        assert transform_completion["result"]["outcome"]["reason_code"]=={
            "missing-required":"derivation_required_port","cross-context":"material_context_or_bytes"}[case]
        assert not transform_completion["result"]["outcome"]["retryable"]
    else:
        confirm(transformed,transform_completion)
        # Historical acceptance must survive owner replacement; no old live lease.
        stop("runtime");stop("data")
        start("data",Path(environment["QUAL_DATA_PYTHON"]),data_port,environment)
        start("runtime",Path(environment["QUAL_RUNTIME_PYTHON"]),runtime_port,environment)
        ready_step()
        receipt,completion=execute(["-m","amphora_process_mapping","worker","--operation","derive-process",
            "--config",config("process-derive")],"process-derive")
        assert receipt["outcome"]=="succeeded"
        def read(ref,model):
            connection=http.client.HTTPConnection("127.0.0.1",data_port,timeout=20)
            try:
                connection.request("GET","/v1/artifacts/"+ref.artifact_id+"/content",headers={"Authorization":"Bearer "+"q"*32})
                response=connection.getresponse();raw=response.read();assert response.status==200
                assert len(raw)==ref.size_bytes and hashlib.sha256(raw).hexdigest()==ref.sha256
                return model.model_validate_json(raw)
            finally:connection.close()
        from amphora_contracts_core import ArtifactRef
        root=ArtifactRef.model_validate_json(json.dumps(completion["result"]["outcome"]["outputs"][0]["artifact"]))
        batch=read(root,DerivedMaterialBatch)
        derivation=read(batch.derivation,ProcessDerivation)
        collection=read(batch.collection,MaterialCollection)
        assert derivation.producer.completion_id==transformed["operation_id"] and derivation.tool==ProcessCapability("transform-materials").descriptor("f"*64).tool.binding
        assert len(derivation.inputs)==3 and len(derivation.outputs)==len(collection.items)==2
        assert tuple((use.port,use.ordinal) for use in derivation.inputs)==(("left",0),("left",1),("right",0))
        assert len(derivation.absent)==1 and derivation.absent[0].port=="annotation"
        assert tuple(item.state for item in collection.items)==tuple(use.material for use in derivation.outputs)
        for use in derivation.outputs:
            state=read(use.material,MaterialState)
            assert state.context==batch.context and state.conditions==derivation.conditions
            assert state.amount is state.composition is state.phase is state.material_batch_id is None
            assert {"amount","composition","phase","physical_batch","conservation","reaction_feasibility"}<=set(state.unknowns)
        closure=confirm(receipt,completion);retained=closure["artifact_count"]
        reservation=completion["retention_reservation_ids"][0]
        connection=http.client.HTTPConnection("127.0.0.1",data_port,timeout=20)
        try:
            connection.request("GET","/v1/retention-closures/"+reservation,headers={"Authorization":"Bearer "+"d"*32})
            response=connection.getresponse();assert response.status==403;response.read()
        finally:connection.close()
    for _ in range(8):
        call(runtime_port,"/v1/graph-runs/advance",command("graph.advance",dict(run_id=run,max_transitions=32)))
        state=call(runtime_port,"/v1/runs/"+run)
        if state["status"]!="running":break
    assert state["status"]==("blocked" if failed else "completed") and state["budget"]["spent"]==(2 if failed else 3),state
    write(output/"process-transform-evidence.json",dict(status="passed",case=case,inputs=3,outputs=0 if failed else 2,
        actual_accepted_producer=not failed,owners_restarted=[] if failed else ["data","runtime"],
        run_status=state["status"],spent=state["budget"]["spent"],retained_artifacts=retained,
        worker_retention_grant=False,provider_calls=0))
