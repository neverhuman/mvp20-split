"""Public-record fixture for initial selector; no actual-owner acceptance claim."""
import hashlib
import json
from types import SimpleNamespace

from amphora_contracts_core import ArtifactRef
from amphora_contracts_population_steps import SelectPopulationRequest,population_step_schema
from amphora_evolution_search.population import canonical
from amphora_evolution_search.population_workers.assembly import PrimaryAssembly
from amphora_evolution_search.population_workers.artifacts import PopulationArtifacts
from amphora_evolution_search.population_workers.capabilities import PopulationCapability
from amphora_evolution_search.population_workers.method_plan import plan_bytes

from .assembly_fixture import assembly_fixture
from .test_inspection import Scripted


def selection_fixture(e,status="succeeded"):
    c=assembly_fixture(e,status)
    assembly=PrimaryAssembly.load(c.source,c.session,c.runtime,c.binding)
    fitted=assembly.publish(c.session)
    from amphora_evolution_search.population_workers.payloads import FittedPrimaryGeneration
    record=FittedPrimaryGeneration.model_validate_json(fitted.content)
    request=SelectPopulationRequest(schema_version="1",specification=record.specification,pool=record.pool,
        fitness=record.fitness,resolution=record.resolution,predecessor=None)
    raw=canonical(request)
    carrier=ArtifactRef(artifact_id="selection-input",scope=e.client.identity.scope,sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw),media_type="application/json",schema_ref=population_step_schema("population-step.select"))
    e.client.contents[carrier.artifact_id]=raw
    plan=c.collection.plan.execution
    cut=dict(scope=e.client.identity.scope.model_dump(),run_id=e.attempt.invocation.run_id,plan_sha256=plan.sha256,revision=300,frontier_revision=20)
    def node(name,kind,status):
        path=dict(schema_version="2",node_id=name,occurrences=[])
        address=hashlib.sha256(plan_bytes(dict(profile="amphora-activation-address-v1",plan_sha256=plan.sha256,path=path))).hexdigest()
        return dict(activation_id=address,path=path,kind=kind,status=status,reason_code=None)
    root=[node("evaluate","scatter","succeeded"),node("collect","invoke","succeeded"),node("assemble","invoke","succeeded"),
        node("select","invoke","issued"),node("finish","finish","waiting")]
    detail_map={}
    for method in c.collection.methods:
        entry=method.owner.detail.node.model_dump(mode="json");root.append(entry)
        detail_map[entry["activation_id"]]={**method.owner.detail.model_dump(mode="json"),"cut":cut}
    for entry in root[:5]:
        attempts=[]
        if entry["kind"]=="invoke":
            name=entry["path"]["node_id"]
            attempts=[dict(attempt_id=name+"-attempt",invocation_id=entry["activation_id"],worker_id="worker",fence=1,
                status="leased" if name=="select" else "succeeded",settled=name!="select",
                completion_id=None if name=="select" else name+"-completion",canonical_result=name!="select")]
        detail_map[entry["activation_id"]]=dict(cut=cut,node=entry,scope_key="c"*64,parent_activation_id=None,outputs=[],attempts=attempts,next_cursor=None)
    assembled=next(entry for entry in root if entry["path"]["node_id"]=="assemble")
    own=next(entry for entry in root if entry["path"]["node_id"]=="select")
    invocation=dict(node_id="assemble",activation_id=assembled["activation_id"],invocation_id=assembled["activation_id"],
        tool=c.binding.model_dump(mode="json"),inputs=[dict(port="parameters",artifact=c.source.reference.model_dump(mode="json"))],
        checkpoint=None,timeout_seconds=3600,side_effects="pure")
    completion=dict(scope=cut["scope"],run_id=cut["run_id"],completion_id="assemble-completion",activation_id=assembled["activation_id"],
        accepted_run_revision=290,canonical_result=True,retention_reservation_ids=[],result=dict(schema_version="1",invocation_id=assembled["activation_id"],
        attempt_id="assemble-attempt",fence=1,outcome=dict(status="succeeded",outputs=[dict(port="result",artifact=fitted.reference.model_dump(mode="json"))])))
    inputs=dict(schema_version="1",profile="runtime-node-inputs-v1",scope=cut["scope"],run_id=cut["run_id"],activation_id=assembled["activation_id"],
        scope_key="c"*64,observed_run_revision=300,scope_inputs=[],invocation=invocation)
    proof=dict(wire_version="1",authority="accepted_execution",worker_id="worker",invocation=invocation,completion=completion)
    snapshot=dict(cut=cut,status="running",budget=dict(limit=100,reserved=1,spent=6),query=dict(scope_key=None,frontier_only=False),
        node_count=len(root),snapshot_token="snap",event_cursor="events")
    page=dict(snapshot=snapshot,nodes=root,next_cursor=None)
    responses=[page,detail_map[assembled["activation_id"]],inputs,proof,*[detail_map[entry["activation_id"]] for entry in root if entry["kind"]=="invoke"]]
    e.client.identity.actor_id="worker"
    runtime=SimpleNamespace(identity=e.client.identity,transport=Scripted(responses))
    tool=PopulationCapability("select-primary").descriptor("f"*64).tool.binding
    e.attempt.invocation=SimpleNamespace(activation_id=own["activation_id"],node_id="select",tool=tool,attempt_id="select-attempt",fence=1,
        run_id=cut["run_id"],inputs=(SimpleNamespace(port="parameters",artifact=carrier),),checkpoint=None)
    session=PopulationArtifacts(e.client,e.attempt,c.session.implementation,transformation_id=tool.capability_id)
    return SimpleNamespace(request=request,session=session,runtime=runtime,fitted=fitted,page=page,proof=proof,
        prepared=c.prepared,expected_attempts=sum(len(detail_map[entry["activation_id"]]["attempts"]) for entry in root if entry["kind"]=="invoke"))
