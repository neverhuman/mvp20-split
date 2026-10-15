"""Pure client fixture; definition copied from installed method probe20261015b."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from amphora_contracts_campaigns import ExecutableCampaignV4, ExecutionPlanV4
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population_steps import PopulationMemberSlice,PopulationSliceRequest,SeedPopulationRequest,population_step_schema
from amphora_evolution_search.population import OriginalPopulation,canonical
from amphora_evolution_search.population_workers.artifacts import PopulationArtifacts
from amphora_evolution_search.population_workers.capabilities import PopulationCapability
from amphora_evolution_search.population_workers.method_plan import payload_schema,plan_bytes
from amphora_evolution_search.population_workers.payloads import CollectPrimaryRequest
from amphora_evolution_search.population_workers.seed import SeedPreparation
from amphora_evolution_search.population_workers.slices import SeedSlices
from amphora_evolution_search.population_workers.worker import PopulationWorker

from .test_inspection import Scripted


def fixture(e,status="succeeded", *, assembly_binding=None):
    worker=PopulationWorker(SimpleNamespace(identity=e.client.identity),e.client,PopulationCapability("evaluate-squares"),"f"*64)
    definition=json.loads(Path(__file__).with_name("primary-method-definition.json").read_bytes())
    definition["scope"]=e.original.record.scope.model_dump(mode="json")
    definition["body"]["nodes"][0]["tool"]=worker.tool.binding.model_dump(mode="json")
    definition=ExecutableCampaignV4.model_validate_json(json.dumps(definition))
    def artifact(model,name,label):
        raw=canonical(model)
        reference=ArtifactRef(artifact_id=label,scope=e.original.record.scope,sha256=hashlib.sha256(raw).hexdigest(),
            size_bytes=len(raw),media_type="application/json",schema_ref=payload_schema(type(model),name))
        e.client.contents[label]=raw
        return reference
    def plan(definition):
        raw=definition.model_dump(mode="json")
        document=dict(profile="amphora-execution-plan-v3",definition=raw,
            lock=dict(schema_version="4",compiler_profile="amphora-deterministic-compiler-v3",
                definition_sha256=hashlib.sha256(plan_bytes({"profile":"amphora-executable-definition-v4","definition":raw})).hexdigest(),
                tools=[],schemas=[],context=[]),scopes=[dict(path=[],order=[n.node_id for n in definition.body.nodes],
                    nodes=[dict(node_id=n.node_id,inputs=[],outputs=[]) for n in definition.body.nodes])])
        return ExecutionPlanV4.model_validate_json(json.dumps(dict(schema_version="4",document=document,
            sha256=hashlib.sha256(plan_bytes(document)).hexdigest())))
    method_plan=plan(definition)
    method=e.original.record.method_graph.methods[0].model_copy(update={"node_path":("cost",),"tool":worker.tool.binding,
        "input_schema":worker.tool.inputs[0].schema_ref,"output_schema":worker.tool.outputs[0].schema_ref})
    graph=e.original.record.method_graph.model_copy(update={"methods":(method,),"definition":artifact(definition,"test.method-definition","method-definition"),
        "plan_sha256":method_plan.sha256})
    objective=e.original.record.assembly.objectives[0].model_copy(update={"method_ids":(method.method_id,)})
    assembly=e.original.record.assembly.model_copy(update={"objectives":(objective,)})
    constraints=e.original.record.constraints
    if assembly_binding is not None:
        from amphora_evolution_search.population_workers.payloads import PrimarySumPolicy,UnconstrainedSynthetic
        assembly=assembly.model_copy(update={"tool":assembly_binding,"policy":artifact(
            PrimarySumPolicy(schema_version="1",profile="primary-dimensionless-sum-v1"),"population-worker.fitness-policy","fitness-policy")})
        constraints=artifact(UnconstrainedSynthetic(schema_version="1",profile="unconstrained-synthetic-v1"),
            "population-worker.synthetic-constraints","fitness-constraints")
    original=OriginalPopulation(e.original.record.model_copy(update={"method_graph":graph,"implementations":(worker.implementation,),
        "assembly":assembly,"constraints":constraints,
        "budget":e.original.record.budget.model_copy(update={"population_size":4,"dispatch_slice":4})}))
    raw=canonical(original.record);spec=e.source.model_copy(update={"sha256":hashlib.sha256(raw).hexdigest(),"size_bytes":len(raw)})
    e.client.contents[spec.artifact_id]=raw
    session=PopulationArtifacts(e.client,e.attempt,worker.implementation)
    root=SeedPreparation.load(SeedPopulationRequest(schema_version="1",specification=spec),session).publish(session)
    prepared=SeedSlices.load(root.reference,session)
    sliced=prepared.publish(PopulationSliceRequest(schema_version="1",prepared=root.reference,start_index=0,limit=4),session)
    members=sliced.decode(PopulationMemberSlice,population_step_schema("population-step.member-slice"),e.original.record.scope).members
    body=definition.body.model_dump(mode="json");result_shape=body["outputs"][0]["value_type"]
    context_shape=body["inputs"][0]["value_type"]
    execution=definition.model_dump(mode="json");execution["campaign_id"]="test-population"
    execution["body"]={"inputs":[],"outputs":[],"nodes":[dict(kind="scatter",node_id="evaluate",
        collection=dict(kind="input",name="members"),item_input="candidate",captures=[],max_members=32,max_parallel=4,
        body=body,result_port="result",output=dict(name="result",value_type=dict(kind="collection",item=result_shape,max_items=32,missing_slots=False)),
        policy=dict(kind="all"))],"edges":[]}
    if assembly_binding is not None:
        collector=worker.tool.binding.model_copy(update={"capability_id":"numeric.population-collect-primary"})
        for name,binding in (("collect",collector),("assemble",assembly_binding),
                ("select",collector.model_copy(update={"capability_id":"numeric.population-select-primary"}))):
            execution["body"]["nodes"].append(dict(kind="invoke",node_id=name,tool=binding.model_dump(mode="json"),
                inputs=[],timeout_seconds=3600,checkpoint=None))
        execution["body"]["nodes"].append(dict(kind="finish",node_id="finish",outputs=[]))
        execution["body"]["edges"]=[dict(source=a["node_id"],target=b["node_id"],route="next")
            for a,b in zip(execution["body"]["nodes"],execution["body"]["nodes"][1:])]
    execution=plan(ExecutableCampaignV4.model_validate_json(json.dumps(execution)))
    request=CollectPrimaryRequest(schema_version="1",prepared=root.reference,
        execution_plan=artifact(execution,"test.execution-plan","execution-plan"),
        method_plan=artifact(method_plan,"test.method-plan","method-plan"),method_scope_path=("evaluate",))
    cut=dict(scope=e.original.record.scope.model_dump(mode="json"),run_id=e.attempt.invocation.run_id,
        plan_sha256=execution.sha256,revision=100,frontier_revision=10)
    nodes=[];responses=[]
    for index,reference in enumerate(members):
        path=dict(schema_version="2",node_id="cost",occurrences=[dict(kind="scatter",node_id="evaluate",index=index,membership_sha256="b"*64)])
        address=hashlib.sha256(plan_bytes(dict(profile="amphora-activation-address-v1",plan_sha256=execution.sha256,path=path))).hexdigest()
        current_status="skipped" if status=="all-skipped" else status if index==0 else "succeeded"
        node=dict(activation_id=address,path=path,kind="invoke",status=current_status,reason_code=None)
        node["reason_code"]="conditional_not_taken" if current_status=="skipped" else "tool_failed" if current_status=="failed" else None
        if current_status=="blocked":node["reason_code"]="graph_dependency_unavailable"
        nodes.append(node)
        invocation=dict(node_id="cost",activation_id=address,invocation_id=address,tool=worker.tool.binding.model_dump(mode="json"),
            inputs=[dict(port="parameters",artifact=reference.model_dump(mode="json"))],checkpoint=None,timeout_seconds=3600,side_effects="pure")
        attempt=dict(attempt_id="attempt-"+str(index),invocation_id=address,worker_id="worker",fence=1,status=current_status,
            settled=True,completion_id="completion-"+str(index),canonical_result=True)
        if current_status in {"skipped","blocked"}:attempts=[];invocation=None
        else:attempts=[attempt]
        detail=dict(cut=cut,node=node,scope_key="c"*64,parent_activation_id="d"*64,outputs=[],attempts=attempts,next_cursor=None)
        inputs=dict(schema_version="1",profile="runtime-node-inputs-v1",scope=cut["scope"],run_id=cut["run_id"],activation_id=address,
            scope_key="c"*64,observed_run_revision=100,scope_inputs=[dict(port="candidate",kind="artifact",item_count=1,missing_count=0,
                artifact=reference.model_dump(mode="json"))],invocation=invocation)
        responses.extend([detail,inputs])
        if current_status not in {"skipped","blocked"}:
            if current_status=="succeeded":
                e.attempt.invocation.node_id="cost";e.attempt.invocation.inputs=(SimpleNamespace(port="parameters",artifact=reference),)
                e.attempt.invocation.attempt_id=attempt["attempt_id"]
                outcome=worker.execute(e.attempt)
                assert outcome["status"]=="succeeded"
            else:outcome=dict(status="failed",reason_code="fixture_failure",retryable=False)
            completion=dict(scope=cut["scope"],run_id=cut["run_id"],completion_id=attempt["completion_id"],activation_id=address,
                accepted_run_revision=90,canonical_result=True,retention_reservation_ids=[],
                result=dict(schema_version="1",invocation_id=address,attempt_id=attempt["attempt_id"],fence=1,outcome=outcome))
            responses.append(dict(wire_version="1",authority="accepted_execution",worker_id="worker",invocation=invocation,completion=completion)
                if current_status=="succeeded" else completion)
    snapshot=dict(cut=cut,status="running",budget=dict(limit=100,reserved=1,spent=6),query=dict(scope_key=None,frontier_only=False),
        node_count=len(nodes),snapshot_token="snapshot",event_cursor="events")
    page=dict(snapshot=snapshot,nodes=nodes,next_cursor=None)
    transport=Scripted([page,*responses]);runtime=SimpleNamespace(identity=e.client.identity,transport=transport)
    e.attempt.invocation.attempt_id="collector";e.attempt.invocation.inputs=()
    session=PopulationArtifacts(e.client,e.attempt,worker.implementation)
    return SimpleNamespace(request=request,session=session,runtime=runtime,page=page,responses=responses,prepared=prepared.prepared,
        nodes=nodes,transport=transport,original=original)
