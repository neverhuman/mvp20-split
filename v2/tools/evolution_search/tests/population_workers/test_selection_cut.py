"""Closed-cut counter policy over public plan/observation records."""
import hashlib
import json
from types import SimpleNamespace

import pytest
from amphora_contracts_campaigns import ExecutionPlanV4
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import GraphNodeViewV3,GraphReadSnapshot
from amphora_evolution_search.population_workers.capabilities import PopulationCapability
from amphora_evolution_search.population_workers.inspection import GraphCapture,PopulationInspection
from amphora_evolution_search.population_workers.method_plan import plan_bytes
from amphora_evolution_search.population_workers.selection_cut import SelectionReadCut

from .conftest import Attempt
from .test_inspection import Scripted


def counter_case(*,parallel=False,loop=False,finish_barrier=True,missing_own_attempt=False):
    scope=Scope(tenant_id="counter",project_id="fixture")
    tool=PopulationCapability("select-primary").descriptor("f"*64).tool.binding
    invokes=[dict(kind="invoke",node_id=name,tool=tool.model_dump(mode="json"),inputs=[],timeout_seconds=60,checkpoint=None)
        for name in ("source","select","future")]
    body=dict(inputs=[],outputs=[],nodes=[*invokes,dict(kind="finish",node_id="finish",outputs=[])],
        edges=[dict(source=a,target=b,route="next") for a,b in (("source","select"),("select","future"),("future","finish")) if finish_barrier or a!="select"])
    occurrences=[]
    definition=dict(schema_version="4",profile="deterministic-v3",campaign_id="counter",revision=1,scope=scope.model_dump(),context=[],body=body)
    root_nodes=[]
    if loop:
        definition["body"]=dict(inputs=[],outputs=[],nodes=[dict(kind="iterate",node_id="generation",state=[dict(name="i",value_type=dict(kind="scalar",scalar="integer",unit="1"),
            initial=dict(kind="integer",value=0,unit="1"),feedback_port="i")],captures=[],body=body,until=dict(kind="constant",value=False),max_iterations=2,on_limit="finish"),
            dict(kind="finish",node_id="root-finish",outputs=[])],edges=[dict(source="generation",target="root-finish",route="next")])
        occurrences=[dict(kind="loop",node_id="generation",index=0)]
    document=dict(profile="amphora-execution-plan-v3",definition=definition,
        lock=dict(schema_version="4",compiler_profile="amphora-deterministic-compiler-v3",definition_sha256="0"*64,tools=[],schemas=[],context=[]),
        scopes=[dict(path=[],order=["select"],nodes=[dict(node_id="select",inputs=[],outputs=[])])])
    plan=ExecutionPlanV4.model_validate_json(json.dumps(dict(schema_version="4",sha256=hashlib.sha256(plan_bytes(document)).hexdigest(),document=document)))
    def node(name,kind,status,occ=occurrences):
        path=dict(schema_version="2",node_id=name,occurrences=occ)
        address=hashlib.sha256(plan_bytes(dict(profile="amphora-activation-address-v1",plan_sha256=plan.sha256,path=path))).hexdigest()
        return GraphNodeViewV3.model_validate_json(json.dumps(dict(activation_id=address,path=path,kind=kind,status=status,reason_code=None)))
    nodes=[node("source","invoke","succeeded"),node("select","invoke","issued"),
        node("future","invoke","issued" if parallel else "waiting"),node("finish","finish","waiting")]
    if loop:nodes=[node("generation","iterate","ready",[]),node("root-finish","finish","waiting",[]),*nodes]
    cut=dict(scope=scope.model_dump(),run_id="run",plan_sha256=plan.sha256,revision=10,frontier_revision=2)
    snapshot=GraphReadSnapshot.model_validate_json(json.dumps(dict(cut=cut,status="running",budget=dict(limit=20,reserved=1,spent=1),
        query=dict(scope_key=None,frontier_only=False),node_count=len(nodes),snapshot_token="snap",event_cursor="events")))
    replies=[]
    for entry in nodes:
        if entry.kind!="invoke":continue
        attempts=[]
        if entry.path.node_id in {"source","select"} and not (missing_own_attempt and entry.path.node_id=="select"):
            attempts=[dict(attempt_id=entry.path.node_id+"-attempt",invocation_id=entry.activation_id,worker_id="selector",fence=1,
                status="succeeded" if entry.path.node_id=="source" else "leased",settled=entry.path.node_id=="source",
                completion_id="done" if entry.path.node_id=="source" else None,canonical_result=entry.path.node_id=="source")]
        replies.append(dict(cut=cut,node=entry.model_dump(mode="json"),scope_key="c"*64,parent_activation_id=None,outputs=[],attempts=attempts,next_cursor=None))
    own=next(node for node in nodes if node.path.node_id=="select")
    attempt=Attempt();attempt.invocation=SimpleNamespace(activation_id=own.activation_id,node_id="select",tool=tool,
        attempt_id="select-attempt",fence=1,run_id="run")
    runtime=SimpleNamespace(identity=SimpleNamespace(scope=scope,actor_id="selector"),transport=Scripted(replies))
    return PopulationInspection(runtime,attempt),GraphCapture(snapshot,tuple(nodes)),plan


@pytest.mark.parametrize("loop",[False,True])
def test_exact_attempt_and_materialized_node_counts_include_current_claim(loop):
    inspection,capture,plan=counter_case(loop=loop)
    result=SelectionReadCut.load(inspection,capture,plan)
    assert result.attempts_issued==2 and result.activations_created==(6 if loop else 4)
    assert result.cut==capture.snapshot.cut


@pytest.mark.parametrize("options,reason",[({"parallel":True},"parallel_work"),
    ({"finish_barrier":False},"finish_barrier"),({"missing_own_attempt":True},"attempt_owner")])
def test_unclosed_or_unowned_counter_cut_rejects(options,reason):
    inspection,capture,plan=counter_case(**options)
    with pytest.raises(ValueError,match=reason):SelectionReadCut.load(inspection,capture,plan)
