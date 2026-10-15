"""Actual independently installed mapping worker over ordinary owner HTTP APIs."""
import hashlib
import http.client
import json
import subprocess
from pathlib import Path

from amphora_contracts_population import MaterialState,MaterialMappingManifest,MaterialMappingPage,population_record_schema
from amphora_process_mapping.capability import MappingCapability,SCHEMAS
from amphora_process_mapping.payloads import payload_schema
from verify_retention_closure_installation import ROOT,write


def release_lock(descriptor):
    raw=json.dumps(dict(profile="amphora-tool-release-v1",descriptor=descriptor),sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
    return dict(schema_version="1",tool=descriptor["tool"]["binding"],descriptor_sha256=hashlib.sha256(raw).hexdigest(),
        checkpoint_schema=None,input_schemas=[dict(port="parameters",schema_ref=descriptor["tool"]["inputs"][0]["schema_ref"])],
        output_schemas=[dict(port="result",schema_ref=descriptor["tool"]["outputs"][0]["schema_ref"])])


def verify(output,python,ports,environment,scope,call,command,start,stop,*,case="pairwise"):
    data_port,runtime_port=ports
    result=subprocess.run([str(python),"-I","-m","amphora_process_mapping","describe","--image-sha256","f"*64],capture_output=True,timeout=120)
    assert result.returncode==0,"Installed mapping descriptor failed"
    descriptor=json.loads(result.stdout)
    write(output/"mapping-release.json",descriptor)
    capability=MappingCapability()
    assert descriptor==capability.descriptor("f"*64).model_dump(mode="json")
    fixture_schema={"type":"object","properties":{"case":{"enum":["pairwise","keyed","cartesian","cross-context"]}},
        "required":["case"],"additionalProperties":False}
    raw=(json.dumps(fixture_schema,sort_keys=True,separators=(",",":"))+"\n").encode()
    fixture_ref=dict(schema_id="fixture.material-source",version="1",sha256=hashlib.sha256(raw).hexdigest())
    (output/"material-source-schema.json").write_bytes(raw)
    source=json.loads(json.dumps(descriptor))
    source["tool"]["binding"]["capability_id"]="fixture.material-source"
    source["tool"]["purpose"]="Admitted test-only synthetic material source; no scientific inference."
    source["tool"]["inputs"][0].update(schema_ref=fixture_ref,representation="fixture-material-source-v1")
    source["tool"]["outputs"][0].update(schema_ref=descriptor["tool"]["inputs"][0]["schema_ref"])
    write(output/"material-source-release.json",source)
    data=json.loads((output/"data.json").read_bytes())
    schemas=[]
    for name,(model,schema_id) in (*SCHEMAS.items(),("state",(MaterialState,"population.material-state"))):
        schema_raw=payload_schema(model,schema_id)
        reference=dict(schema_id=schema_id,version="1",sha256=hashlib.sha256(schema_raw).hexdigest())
        if name in {"state","page","manifest"}:assert reference==population_record_schema(schema_id).model_dump()
        filename="process-"+name+"-schema.json"
        (output/filename).write_bytes(schema_raw)
        data["profiles"].append(dict(media_type="application/json",**reference,schema_path=filename))
        schemas.append(dict(schema_ref=reference,path=filename))
    data["profiles"].append(dict(media_type="application/json",**fixture_ref,schema_path="material-source-schema.json"))
    principals=[]
    for actor,token in (("process-source","s"*32),("process-mapper","m"*32)):
        token_env="QUAL_"+actor.replace("-","_").upper()+"_TOKEN"
        environment[token_env]=token
        principal=dict(actor_id=actor,scope=scope,token_env=token_env)
        data["principals"].append(dict(**principal,actions=["read","upload","finalize"]))
        principals.append(dict(**principal,actions=["claim","renew","complete","read"]))
    write(output/"data.json",data)
    def shape(port):return dict(kind="artifact",schema_ref=port["schema_ref"],representation=port["representation"],unit="1",media_type="application/json")
    nodes=[]
    for name,release,origin in (("source",source,dict(kind="input",name="parameters")),
            ("map",descriptor,dict(kind="output",node_id="source",port="result"))):
        nodes.append(dict(kind="invoke",node_id=name,tool=release["tool"]["binding"],
            inputs=[dict(port="parameters",source=origin)],timeout_seconds=3600,checkpoint=None))
    nodes.append(dict(kind="finish",node_id="finish",outputs=[dict(port="result",source=dict(kind="output",node_id="map",port="result"))]))
    definition=dict(schema_version="4",profile="deterministic-v3",campaign_id="process-map-fixture",revision=1,scope=scope,context=[],
        body=dict(inputs=[dict(name="parameters",value_type=shape(source["tool"]["inputs"][0]))],
            outputs=[dict(name="result",value_type=shape(descriptor["tool"]["outputs"][0]))],nodes=nodes,
            edges=[dict(source="source",target="map",route="next"),dict(source="map",target="finish",route="next")]))
    write(output/"process-graph.json",definition)
    runtime=json.loads((output/"runtime.json").read_bytes())
    runtime["bindings"]=dict(endpoint=f"http://127.0.0.1:{data_port}",token_env="QUAL_TOKEN")
    environment["QUAL_PROCESS_CURSOR_KEY"]="k"*64
    runtime["inspection"]=dict(cursor_key_env="QUAL_PROCESS_CURSOR_KEY")
    runtime["principals"][0]["actions"].append("inspect_receipts")
    runtime["principals"].extend(principals)
    runtime["graphs"]=[dict(definition="process-graph.json",releases=[dict(descriptor=filename,lock=release_lock(release))
        for filename,release in (("material-source-release.json",source),("mapping-release.json",descriptor))],
        schemas=[*schemas,dict(schema_ref=fixture_ref,path="material-source-schema.json")])]
    write(output/"runtime.json",runtime)
    stop("runtime");stop("data")
    start("data",Path(environment["QUAL_DATA_PYTHON"]),data_port,environment)
    ready=start("runtime",Path(environment["QUAL_RUNTIME_PYTHON"]),runtime_port,environment)
    raw=json.dumps(dict(case=case),sort_keys=True,separators=(",",":" )).encode()
    begin=call(data_port,"/v1/uploads",command("artifacts.begin_upload",dict(content=dict(sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw),media_type="application/json",schema_ref=fixture_ref))))
    upload=begin["upload_id"]
    connection=http.client.HTTPConnection("127.0.0.1",data_port,timeout=20)
    try:
        connection.request("PUT","/v1/uploads/"+upload+"/content",raw,headers={"Authorization":"Bearer "+"q"*32})
        response=connection.getresponse();assert response.status==200;response.read()
    finally:connection.close()
    artifact=call(data_port,"/v1/artifacts/finalize",command("artifacts.finalize",dict(upload_id=upload,content=begin["content"])))["artifact"]
    admission=call(runtime_port,"/v1/graph-runs",command("graph.admit",dict(plan_sha256=ready["plan_sha256"],
        inputs=[dict(port="parameters",value=dict(kind="artifact",artifact=artifact,representation="fixture-material-source-v1",unit="1"))],budget=dict(limit=2))))
    run=admission["outcome"]["committed"]["object_id"]
    def worker_config(actor):
        token_env="QUAL_"+actor.replace("-","_").upper()+"_TOKEN"
        path=output/(actor+"-worker.json")
        write(path,dict(actor_id=actor,scope=scope,run_id=run,image_sha256="f"*64,lease_seconds=60,
            runtime=dict(endpoint=f"http://127.0.0.1:{runtime_port}",token_env=token_env),
            artifacts=dict(endpoint=f"http://127.0.0.1:{data_port}",token_env=token_env)))
        return path
    def run_worker(args,label):
        result=subprocess.run([str(python),"-I",*map(str,args)],env=environment,capture_output=True,timeout=1200)
        (output/(label+".log")).write_bytes(result.stdout+result.stderr)
        assert result.returncode==0,"Actual process worker failed; inspect "+label+".log"
        receipt=json.loads(result.stdout)
        completion=call(runtime_port,f"/v1/runs/{run}/completions/"+receipt["operation_id"])
        assert completion["canonical_result"]
        return receipt,completion
    source_receipt,source_completion=run_worker([ROOT/"dev/process_material_bootstrap.py",worker_config("process-source"),
        output/"material-source-release.json"],"material-source")
    assert source_receipt["outcome"]=="succeeded"
    reservation=source_completion["retention_reservation_ids"][0]
    binding=call(data_port,"/v1/retention-closures/"+reservation)["reservation"]["outcome"]["binding"]
    call(data_port,"/v1/reservations/confirm",command("artifacts.confirm",dict(reservation_id=reservation,
        intent_id=binding["intent"]["intent_id"],runtime_receipt_id=source_receipt["operation_id"])))
    call(runtime_port,"/v1/graph-runs/advance",command("graph.advance",dict(run_id=run,max_transitions=32)))
    receipt,completion=run_worker(["-m","amphora_process_mapping","worker","--config",worker_config("process-mapper")],"mapping-worker")
    failed=case=="cross-context"
    assert receipt["outcome"]==("failed" if failed else "succeeded")
    retained=0;pairs=excluded=0
    if failed:
        assert completion["result"]["outcome"]["reason_code"]=="invalid_process_mapping"
        assert not completion["result"]["outcome"]["retryable"]
    else:
        root=completion["result"]["outcome"]["outputs"][0]["artifact"]
        def read(ref):
            connection=http.client.HTTPConnection("127.0.0.1",data_port,timeout=20)
            try:
                connection.request("GET","/v1/artifacts/"+ref["artifact_id"]+"/content",headers={"Authorization":"Bearer "+"q"*32})
                response=connection.getresponse();raw=response.read();assert response.status==200
                assert len(raw)==ref["size_bytes"] and hashlib.sha256(raw).hexdigest()==ref["sha256"]
                return raw
            finally:connection.close()
        manifest=MaterialMappingManifest.model_validate_json(read(root))
        pages=[MaterialMappingPage.model_validate_json(read(ref.artifact.model_dump(mode="json"))) for ref in manifest.pages]
        pairs=sum(len(page.pairs) for page in pages);excluded=sum(len(page.excluded) for page in pages)
        assert (pairs,excluded)=={"pairwise":(2,0),"keyed":(1,1),"cartesian":(4,0)}[case]
        assert manifest.context.generation.run_id==run and pairs==manifest.pair_count and excluded==manifest.excluded_count
        derivation=call(data_port,"/v1/artifacts/"+root["artifact_id"]+"/derivation")["declaration"]
        assert derivation["transformation"]["transformation_id"]==descriptor["tool"]["binding"]["capability_id"]
        assert {manifest.left.artifact_id,manifest.right.artifact_id}<={ref["artifact_id"] for ref in derivation["inputs"]}
        reservation=completion["retention_reservation_ids"][0]
        closure=call(data_port,"/v1/retention-closures/"+reservation)
        retained=closure["artifact_count"]
        binding=closure["reservation"]["outcome"]["binding"]
        call(data_port,"/v1/reservations/confirm",command("artifacts.confirm",dict(reservation_id=reservation,
            intent_id=binding["intent"]["intent_id"],runtime_receipt_id=receipt["operation_id"])))
    for _ in range(8):
        call(runtime_port,"/v1/graph-runs/advance",command("graph.advance",dict(run_id=run,max_transitions=32)))
        state=call(runtime_port,"/v1/runs/"+run)
        if state["status"]!="running":break
    assert state["status"]==("blocked" if failed else "completed") and state["budget"]["spent"]==2,state
    write(output/"process-mapping-evidence.json",dict(status="passed",case=case,pairs=pairs,excluded=excluded,
        run_status=state["status"],spent=2,retained_artifacts=retained,worker_retention_grant=False,provider_calls=0))
