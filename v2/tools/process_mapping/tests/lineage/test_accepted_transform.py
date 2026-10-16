"""Immutable accepted source proof, distinct from current assembler authority."""
import json
from types import SimpleNamespace

import pytest
from amphora_contracts_population import ProcessDerivation
from amphora_contracts_tools import ToolBinding
from amphora_process_mapping.artifacts import ProcessArtifacts
from amphora_process_mapping.derivation import DerivationAssembly
from amphora_process_mapping.transform import TransformPreparation
from amphora_process_mapping.payloads import (DeriveProcessRequest,DerivedMaterialBatch,
    MaterialCollection,ProposedProcessTransform,schema_ref)

from ..mapping.test_publication import Attempt
from .test_transform import transform_case


class Transport:
    def __init__(self,responses):self.responses=responses;self.calls=[]
    def request(self,method,path,**kwargs):
        assert method=="GET"
        self.calls.append((path,kwargs))
        return SimpleNamespace(status=200,body=json.dumps(self.responses.pop(0)).encode())


def accepted_case(factory):
    request,carrier,original,client=transform_case(factory)
    client.identity.actor_id="transform-worker"
    source=TransformPreparation.load(request,original).publish(original,carrier.reference)
    result=source.decode(ProposedProcessTransform,schema_ref(ProposedProcessTransform,"process-worker.transform-result"),original.scope)
    context=request.context;locator=result.source
    detail=dict(cut=dict(scope=context.generation.scope.model_dump(mode="json"),run_id=context.generation.run_id,
        plan_sha256="a"*64,revision=10,frontier_revision=2),node=dict(activation_id=locator.activation_id,
        path=dict(schema_version="2",node_id="transform",occurrences=[]),kind="invoke",status="succeeded",reason_code=None),
        scope_key="c"*64,parent_activation_id=None,outputs=[],next_cursor=None,attempts=[dict(
            attempt_id=locator.attempt_id,invocation_id=locator.invocation_id,fence=locator.fence,worker_id="transform-worker",
            status="succeeded",settled=True,completion_id="accepted-completion",canonical_result=True)])
    invocation=dict(node_id="transform",activation_id=locator.activation_id,invocation_id=locator.invocation_id,
        tool=request.binding.tool.model_dump(mode="json"),inputs=[dict(port="parameters",artifact=carrier.reference.model_dump(mode="json"))],
        checkpoint=None,timeout_seconds=3600,side_effects="pure")
    completion=dict(scope=context.generation.scope.model_dump(mode="json"),run_id=context.generation.run_id,
        completion_id="accepted-completion",activation_id=locator.activation_id,accepted_run_revision=9,
        canonical_result=True,retention_reservation_ids=["reservation"],result=dict(schema_version="1",
            invocation_id=locator.invocation_id,attempt_id=locator.attempt_id,fence=locator.fence,
            outcome=dict(status="succeeded",outputs=[dict(port="result",artifact=source.reference.model_dump(mode="json"))],checkpoint=None)))
    proof=dict(wire_version="1",authority="accepted_execution",worker_id="transform-worker",invocation=invocation,completion=completion)
    derive=DeriveProcessRequest(schema_version="1",profile="synthetic-derive-process-v1",result=source.reference)
    artifact=factory[3]("derive-request",schema_ref(DeriveProcessRequest,"process-worker.derive-request"),derive)
    client.contents[artifact.reference.artifact_id]=artifact.content
    client.identity.actor_id="derive-worker"
    own=SimpleNamespace(inputs=(SimpleNamespace(port="parameters",artifact=artifact.reference),),
        run_id=context.generation.run_id,attempt_id="derive-attempt",activation_id="e"*64,invocation_id="derive-invoke",fence=1,
        checkpoint=None,tool=ToolBinding(capability_id="process.synthetic-derive-process",release="0.3.0",image_sha256="f"*64,contract_version="1"))
    session=ProcessArtifacts(client,Attempt(own),"0.3.0","f"*64)
    runtime=SimpleNamespace(identity=client.identity,transport=Transport([detail,proof]))
    unrelated={**detail["node"],"activation_id":"f"*64,
        "path":dict(schema_version="2",node_id="unrelated",occurrences=[]),"status":"waiting"}
    page=dict(snapshot=dict(cut=detail["cut"],status="running",budget=dict(limit=10,reserved=1,spent=2),
        query=dict(scope_key=None,frontier_only=False),node_count=5,snapshot_token="snapshot",event_cursor="events"),
        nodes=[unrelated],next_cursor="unneeded-next-page")
    runtime.transport.responses.insert(0,page)
    original.attempt.active=False
    return SimpleNamespace(request=derive,source=source,result=result,session=session,runtime=runtime,client=client,
        tool=request.binding.tool,detail=detail,proof=proof)


def test_only_actual_accepted_completion_creates_typed_derivation(material_factory):
    c=accepted_case(material_factory);before=len(c.client.uploads)
    assembled=DerivationAssembly.load(c.request,c.session,c.runtime,c.tool)
    root=assembled.publish(c.session)
    batch=root.decode(DerivedMaterialBatch,schema_ref(DerivedMaterialBatch,"process-worker.derived-batch"),c.session.scope)
    record=ProcessDerivation.model_validate_json(c.client.contents[batch.derivation.artifact_id])
    assert record.producer.completion_id=="accepted-completion" and record.producer.attempt_id=="attempt"
    assert record.tool==c.tool and record.producer.attempt_id!=c.session.attempt.invocation.attempt_id
    collection=MaterialCollection.model_validate_json(c.client.contents[batch.collection.artifact_id])
    assert tuple(item.state for item in collection.items)==tuple(use.material for use in c.result.outputs)
    assert len(c.client.uploads)==before+3 and len(c.runtime.transport.calls)==3
    assert c.runtime.transport.calls[0][1]==dict(query=dict(limit=1))
    assert c.runtime.transport.calls[1][1]["query"]["snapshot_token"]=="snapshot"
    assert c.source.reference in c.client.declarations[batch.derivation.artifact_id].inputs
    assert c.client.declarations[batch.derivation.artifact_id].transformation.transformation_id=="process.synthetic-derive-process"


def test_signed_snapshot_and_detail_are_not_invalidated_by_our_own_renewal(material_factory):
    c=accepted_case(material_factory)
    observed=[];original=c.runtime.transport.request
    def observe(method,path,**kwargs):
        observed.append(c.session.attempt.refreshes)
        return original(method,path,**kwargs)
    c.runtime.transport.request=observe
    DerivationAssembly.load(c.request,c.session,c.runtime,c.tool)
    assert len(observed)==3 and observed[0]==observed[1] and observed[2]>observed[1]


@pytest.mark.parametrize("damage,reason",[("canonical","not_accepted"),("attempt","source_attempt"),
    ("fence","source_attempt"),("scope","source_snapshot"),("output","source_binding"),
    ("completion","source_completion"),("origin","source_origin"),("child","source_digest")])
def test_forged_or_inconsistent_source_fails_before_assembler_publication(material_factory,damage,reason):
    c=accepted_case(material_factory);before=len(c.client.uploads)
    if damage=="canonical":c.detail["attempts"][0]["canonical_result"]=False
    if damage=="attempt":c.detail["attempts"][0]["attempt_id"]="other"
    if damage=="fence":c.detail["attempts"][0]["fence"]=2
    if damage=="scope":c.detail["cut"]["scope"]["project_id"]="another"
    if damage=="output":c.proof["completion"]["result"]["outcome"]["outputs"][0]["artifact"]["sha256"]="e"*64
    if damage=="completion":c.proof["completion"]["canonical_result"]=False
    if damage=="origin":
        key=c.source.reference.artifact_id
        c.client.origins[key]=c.client.origins[key].model_copy(update={"actor_id":"another"})
    if damage=="child":c.client.contents[c.result.outputs[0].material.artifact_id]=b"corrupt"
    with pytest.raises(ValueError,match=reason):DerivationAssembly.load(c.request,c.session,c.runtime,c.tool).publish(c.session)
    assert len(c.client.uploads)==before
