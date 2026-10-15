"""Scripted macro acceptance on public owner DTOs; actual-owner evidence is separate."""
import hashlib
from types import SimpleNamespace

from amphora_contracts_core import ArtifactRef
from amphora_contracts_tools import ToolBinding
from amphora_evolution_search.population import canonical
from amphora_evolution_search.population_workers.artifacts import PopulationArtifacts
from amphora_evolution_search.population_workers.capabilities import PopulationCapability
from amphora_evolution_search.population_workers.collection import PrimaryCollection
from amphora_evolution_search.population_workers.method_plan import payload_schema,plan_bytes
from amphora_evolution_search.population_workers.payloads import CollectPrimaryRequest

from .collection_fixture import fixture
from .test_inspection import Scripted


def assembly_fixture(e,status="succeeded"):
    binding=ToolBinding(capability_id="numeric.population-assemble-primary",release=PopulationCapability("seed").release,
        image_sha256="f"*64,contract_version="1")
    c=fixture(e,status,assembly_binding=binding)
    collection=PrimaryCollection.load(c.request,c.session,c.runtime)
    raw=canonical(c.request)
    carrier=ArtifactRef(artifact_id="collector-input",scope=e.client.identity.scope,sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw),media_type="application/json",schema_ref=payload_schema(CollectPrimaryRequest,"population-worker.collect-request"))
    e.client.contents[carrier.artifact_id]=raw
    c.session.attempt.invocation.inputs=(SimpleNamespace(port="parameters",artifact=carrier),)
    c.session.transformation_id="numeric.population-collect-primary"
    source=collection.publish(c.request,c.session)
    tool=binding.model_copy(update={"capability_id":"numeric.population-collect-primary"})
    path=dict(schema_version="2",node_id="collect",occurrences=[])
    plan_sha=c.page["snapshot"]["cut"]["plan_sha256"]
    address=hashlib.sha256(plan_bytes(dict(profile="amphora-activation-address-v1",plan_sha256=plan_sha,path=path))).hexdigest()
    node=dict(activation_id=address,path=path,kind="invoke",status="succeeded",reason_code=None)
    cut=dict(c.page["snapshot"]["cut"],revision=200)
    snapshot=dict(c.page["snapshot"],cut=cut,node_count=1)
    invocation=dict(node_id="collect",activation_id=address,invocation_id=address,tool=tool.model_dump(mode="json"),
        inputs=[dict(port="parameters",artifact=carrier.model_dump(mode="json"))],checkpoint=None,timeout_seconds=3600,side_effects="pure")
    attempt=dict(attempt_id="collector",invocation_id=address,worker_id="worker",fence=1,status="succeeded",
        settled=True,completion_id="collected-completion",canonical_result=True)
    detail=dict(cut=cut,node=node,scope_key="c"*64,parent_activation_id=None,outputs=[],attempts=[attempt],next_cursor=None)
    inputs=dict(schema_version="1",profile="runtime-node-inputs-v1",scope=cut["scope"],run_id=cut["run_id"],activation_id=address,
        scope_key="c"*64,observed_run_revision=200,scope_inputs=[],invocation=invocation)
    completion=dict(scope=cut["scope"],run_id=cut["run_id"],completion_id="collected-completion",activation_id=address,
        accepted_run_revision=190,canonical_result=True,retention_reservation_ids=[],result=dict(schema_version="1",invocation_id=address,
        attempt_id="collector",fence=1,outcome=dict(status="succeeded",outputs=[dict(port="result",artifact=source.reference.model_dump(mode="json"))])))
    proof=dict(wire_version="1",authority="accepted_execution",worker_id="worker",invocation=invocation,completion=completion)
    page=dict(snapshot=snapshot,nodes=[node],next_cursor=None)
    transport=Scripted([page,detail,inputs,proof]);runtime=SimpleNamespace(identity=e.client.identity,transport=transport)
    e.attempt.invocation.attempt_id="fitness";e.attempt.invocation.inputs=(SimpleNamespace(port="parameters",artifact=source.reference),)
    session=PopulationArtifacts(e.client,e.attempt,c.session.implementation,transformation_id=binding.capability_id)
    return SimpleNamespace(source=source,session=session,runtime=runtime,binding=binding,prepared=c.prepared,
        page=page,detail=detail,proof=proof,collection=collection)
