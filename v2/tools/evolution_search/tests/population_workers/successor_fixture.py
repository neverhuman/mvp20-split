"""Accepted checkpoint/public-history double for preparation; no owner integration claim."""
import copy
import hashlib
from types import SimpleNamespace

from amphora_contracts_core import ArtifactRef
from amphora_contracts_population_steps import ProposePopulationSuccessorRequest,population_step_schema
from amphora_evolution_search.population import OriginalPopulation,canonical
from amphora_evolution_search.population_workers.artifacts import PopulationArtifacts
from amphora_evolution_search.population_workers.capabilities import PopulationCapability
from amphora_evolution_search.population_workers.payloads import SelectedPrimaryGeneration
from amphora_evolution_search.population_workers.selection import InitialSelection

from .selection_fixture import selection_fixture
from .test_inspection import Scripted


def successor_fixture(e,status="succeeded", *, generations=1,available=100):
    e.original=OriginalPopulation(e.original.record.model_copy(update={"budget":e.original.record.budget.model_copy(update={"successor_generations":generations})}))
    c=selection_fixture(e,status)
    selected=InitialSelection.load(c.request,c.session,c.runtime).publish(c.session)
    envelope=SelectedPrimaryGeneration.model_validate_json(selected.content)
    request=ProposePopulationSuccessorRequest(schema_version="1",specification=envelope.specification,checkpoint=envelope.checkpoint)
    raw=canonical(request)
    carrier=ArtifactRef(artifact_id="successor-input",scope=e.client.identity.scope,sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw),media_type="application/json",schema_ref=population_step_schema("population-step.successor"))
    e.client.contents[carrier.artifact_id]=raw
    cut=dict(c.page["snapshot"]["cut"],revision=400)
    root=copy.deepcopy(c.root);details=copy.deepcopy(c.detail_map)
    for entry in root:
        name=entry["path"]["node_id"]
        if name in {"select","successor_request"}:entry["status"]="succeeded"
        if name=="prepare_successor":entry["status"]="issued"
        detail=details[entry["activation_id"]];detail["cut"]=cut;detail["node"]=entry
        if name in {"select","successor_request","prepare_successor"}:
            detail["attempts"]=[dict(attempt_id=name+"-attempt",invocation_id=entry["activation_id"],worker_id="worker",fence=1,
                status="leased" if name=="prepare_successor" else "succeeded",settled=name!="prepare_successor",
                completion_id=None if name=="prepare_successor" else name+"-completion",canonical_result=name!="prepare_successor")]
    count=sum(len(details[node["activation_id"]]["attempts"]) for node in root if node["kind"]=="invoke")
    snapshot=dict(c.page["snapshot"],cut=cut,budget=dict(limit=count+available,reserved=1,spent=count-1))
    page=dict(snapshot=snapshot,nodes=root,next_cursor=None)
    assembler=next(node for node in root if node["path"]["node_id"]=="assemble")
    asm_inputs=copy.deepcopy(c.inputs);asm_inputs["observed_run_revision"]=400
    counter_replies=[details[node["activation_id"]] for node in root if node["kind"]=="invoke"]
    selector=next(node for node in root if node["path"]["node_id"]=="select")
    own=next(node for node in root if node["path"]["node_id"]=="prepare_successor")
    selector_tool=PopulationCapability("select-primary").descriptor("f"*64).tool.binding
    select_carrier=c.session.attempt.invocation.inputs[0].artifact
    invocation=dict(node_id="select",activation_id=selector["activation_id"],invocation_id=selector["activation_id"],tool=selector_tool.model_dump(mode="json"),
        inputs=[dict(port="parameters",artifact=select_carrier.model_dump(mode="json"))],checkpoint=None,timeout_seconds=3600,side_effects="pure")
    inputs=dict(schema_version="1",profile="runtime-node-inputs-v1",scope=cut["scope"],run_id=cut["run_id"],activation_id=selector["activation_id"],
        scope_key="c"*64,observed_run_revision=400,scope_inputs=[],invocation=invocation)
    completion=dict(scope=cut["scope"],run_id=cut["run_id"],completion_id="select-completion",activation_id=selector["activation_id"],
        accepted_run_revision=350,canonical_result=True,retention_reservation_ids=[],result=dict(schema_version="1",invocation_id=selector["activation_id"],
        attempt_id="select-attempt",fence=1,outcome=dict(status="succeeded",outputs=[dict(port="result",artifact=selected.reference.model_dump(mode="json"))])))
    proof=dict(wire_version="1",authority="accepted_execution",worker_id="worker",invocation=invocation,completion=completion)
    responses=[page,details[assembler["activation_id"]],asm_inputs,c.proof,*counter_replies,
        page,details[selector["activation_id"]],inputs,proof,*counter_replies]
    tool=PopulationCapability("prepare-successor").descriptor("f"*64).tool.binding
    e.attempt.invocation=SimpleNamespace(activation_id=own["activation_id"],node_id="prepare_successor",tool=tool,
        attempt_id="prepare_successor-attempt",fence=1,run_id=cut["run_id"],inputs=(SimpleNamespace(port="parameters",artifact=carrier),),checkpoint=None)
    runtime=SimpleNamespace(identity=e.client.identity,transport=Scripted(responses))
    session=PopulationArtifacts(e.client,e.attempt,c.session.implementation,transformation_id=tool.capability_id)
    return SimpleNamespace(request=request,runtime=runtime,session=session,selected=selected,source=c,proof=proof,attempts=count)
