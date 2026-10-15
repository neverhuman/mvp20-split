"""Test-only admitted material source. Runs with independently installed public SDK."""
import json
import sys
import uuid
from pathlib import Path

from amphora_contracts_population import (GenerationIdentity,MaterialState,ProcessContext,
    MaterialMappingItem,MaterialMappingPolicy,population_record_schema)
from amphora_contracts_tools import ToolBinding,Completion
from amphora_contracts_runtime import CompleteInvocation
from amphora_tool_protocol import WorkerConfig,WorkerIdentity,RuntimeClient,ArtifactClient,ToolAttemptContext
from amphora_process_mapping.artifacts import ProcessArtifacts
from amphora_process_mapping.payloads import MaterialCollection,MapMaterialsRequest,schema_ref


def main():
    config=WorkerConfig.model_validate_json(Path(sys.argv[1]).read_bytes())
    descriptor=json.loads(Path(sys.argv[2]).read_bytes())
    binding=ToolBinding.model_validate_json(json.dumps(descriptor["tool"]["binding"]))
    identity=WorkerIdentity(config.actor_id,config.scope)
    runtime=RuntimeClient(config.runtime.transport(),identity)
    artifacts=ArtifactClient(config.artifacts.transport(),identity)
    claimed=runtime.claim(config.run_id,binding,"claim-source-"+uuid.uuid4().hex,lease_seconds=60)
    assert claimed.outcome.status=="claimed"
    attempt=ToolAttemptContext(runtime,claimed.outcome,60)
    session=ProcessArtifacts(artifacts,attempt,binding.release,binding.image_sha256)
    carrier=attempt.invocation.inputs[0].artifact
    source=session.read(carrier)
    variant=json.loads(source.content)["case"]
    context=ProcessContext(generation=GenerationIdentity(scope=config.scope,run_id=config.run_id,
        specification_sha256=carrier.sha256,generation=0,predecessor=None),candidate_id="b"*64,process_batch_id="process-1")
    materials=[]
    for index in range(3 if variant=="keyed" else 4):
        current=context.model_copy(update={"candidate_id":"e"*64}) if variant=="cross-context" and index==3 else context
        record=MaterialState(schema_version="1",profile="synthetic-process-material-v1",context=current,
            state_id="state-"+str(index),revision=1,kind="intermediate",representation=carrier,composition=None,
            material_batch_id="physical-"+str(index),amount=None,phase=None,conditions=carrier,
            unknowns=("composition","amount","phase"))
        materials.append(session.publish(record,population_record_schema("population.material-state"),(carrier,),"material-"+str(index)))
    collections=[]
    for name,entries,keys in (("left",materials[:2],("z","a")),
            ("right",materials[2:],("a",) if variant=="keyed" else ("a","z"))):
        record=MaterialCollection(schema_version="1",profile="synthetic-material-collection-v1",context=context,
            items=tuple(MaterialMappingItem(key=key,state=entry.reference) for key,entry in zip(keys,entries,strict=True)))
        collections.append(session.publish(record,schema_ref(MaterialCollection,"process-worker.material-collection"),
            tuple(entry.reference for entry in entries),name))
    mode=variant if variant in {"pairwise","keyed","cartesian"} else "pairwise"
    request=MapMaterialsRequest(schema_version="1",profile="synthetic-map-materials-v1",context=context,
        policy=MaterialMappingPolicy(mode=mode,unmatched="retain_excluded" if mode=="keyed" else "reject",
            cartesian_opt_in=mode=="cartesian",maximum_outputs=4),left=collections[0].reference,right=collections[1].reference)
    root=session.publish(request,schema_ref(MapMaterialsRequest,"process-worker.map-materials"),
        tuple(entry.reference for entry in collections),"source")
    attempt.refresh()
    invocation=attempt.invocation
    completion=Completion.model_validate_json(json.dumps(dict(schema_version="1",invocation_id=invocation.invocation_id,
        attempt_id=invocation.attempt_id,fence=invocation.fence,outcome=dict(status="succeeded",
            outputs=[dict(port="result",artifact=root.reference.model_dump(mode="json"))],checkpoint=None))))
    receipt=runtime.complete(CompleteInvocation(run_id=config.run_id,completion=completion),
        "complete-"+invocation.attempt_id,guard=attempt.check)
    print(json.dumps(dict(status="completion_accepted",outcome="succeeded",operation_id=receipt.outcome.binding.operation_id)))


if __name__=="__main__":main()
