"""Admitted TEST-ONLY precursor source through independently installed SDK/tool code."""
import json
import sys
import uuid
from pathlib import Path

from amphora_contracts_population import (AbsentProcessInput,GenerationIdentity,MaterialAmount,MaterialState,
    MaterialUse,ProcessBinding,ProcessContext,ProcessPort,population_record_schema)
from amphora_contracts_tools import ToolBinding,Completion
from amphora_contracts_runtime import CompleteInvocation
from amphora_tool_protocol import WorkerConfig,WorkerIdentity,RuntimeClient,ArtifactClient,ToolAttemptContext
from amphora_process_mapping.artifacts import ProcessArtifacts
from amphora_process_mapping.payloads import TransformMaterialsRequest,schema_ref


def main():
    config=WorkerConfig.model_validate_json(Path(sys.argv[1]).read_bytes())
    source_descriptor=json.loads(Path(sys.argv[2]).read_bytes())
    target=json.loads(Path(sys.argv[3]).read_bytes())
    binding=ToolBinding.model_validate_json(json.dumps(source_descriptor["tool"]["binding"]))
    transform=ToolBinding.model_validate_json(json.dumps(target["tool"]["binding"]))
    identity=WorkerIdentity(config.actor_id,config.scope)
    runtime=RuntimeClient(config.runtime.transport(),identity)
    artifacts=ArtifactClient(config.artifacts.transport(),identity)
    claim=runtime.claim(config.run_id,binding,"claim-source-"+uuid.uuid4().hex,lease_seconds=60)
    assert claim.outcome.status=="claimed"
    attempt=ToolAttemptContext(runtime,claim.outcome,60)
    session=ProcessArtifacts(artifacts,attempt,binding.release,binding.image_sha256)
    carrier=attempt.invocation.inputs[0].artifact
    variant=json.loads(session.read(carrier).content)["case"]
    context=ProcessContext(generation=GenerationIdentity(scope=config.scope,run_id=config.run_id,
        specification_sha256=carrier.sha256,generation=0,predecessor=None),candidate_id="b"*64,process_batch_id="process-1")
    materials=[]
    for index in range(3):
        current=context.model_copy(update={"candidate_id":"e"*64}) if variant=="cross-context" and index==2 else context
        state=MaterialState(schema_version="1",profile="synthetic-process-material-v1",context=current,
            state_id="precursor-"+str(index),revision=1,kind="intermediate",representation=carrier,
            composition=carrier,material_batch_id="synthetic-physical-"+str(index),amount=MaterialAmount(value=1.0,unit="g"),
            phase="solid",conditions=carrier,unknowns=("conservation","reaction_feasibility"))
        materials.append(session.publish(state,population_record_schema("population.material-state"),(carrier,),"precursor-"+str(index)))
    ports=(ProcessPort(port="left",required=True,representation=carrier.schema_ref,maximum=2),
        ProcessPort(port="right",required=True,representation=carrier.schema_ref,maximum=1),
        ProcessPort(port="annotation",required=False,representation=carrier.schema_ref,maximum=1))
    configured=ProcessBinding(tool=transform,inputs=ports,
        outputs=(ProcessPort(port="products",required=True,representation=carrier.schema_ref,maximum=2),))
    uses=(MaterialUse(port="left",ordinal=0,material=materials[0].reference),
        MaterialUse(port="left",ordinal=1,material=materials[1].reference),
        MaterialUse(port="right",ordinal=0,material=materials[2].reference))
    request=TransformMaterialsRequest(schema_version="1",profile="synthetic-transform-materials-v1",
        policy="copy-first-representation-v1",context=context,binding=configured,
        inputs=uses[:2] if variant=="missing-required" else uses,
        absent=(AbsentProcessInput(port="annotation",reason_code="not_available"),),conditions=carrier,output_count=2)
    root=session.publish(request,schema_ref(TransformMaterialsRequest,"process-worker.transform-request"),
        tuple(material.reference for material in materials),"source")
    attempt.refresh();invocation=attempt.invocation
    completion=Completion.model_validate_json(json.dumps(dict(schema_version="1",invocation_id=invocation.invocation_id,
        attempt_id=invocation.attempt_id,fence=invocation.fence,outcome=dict(status="succeeded",outputs=[
            dict(port="result",artifact=root.reference.model_dump(mode="json"))],checkpoint=None))))
    receipt=runtime.complete(CompleteInvocation(run_id=config.run_id,completion=completion),
        "complete-"+invocation.attempt_id,guard=attempt.check)
    print(json.dumps(dict(status="completion_accepted",outcome="succeeded",operation_id=receipt.outcome.binding.operation_id)))


if __name__=="__main__":main()
