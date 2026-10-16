"""Expanded work and queue bounds must not confuse batches, scopes and attempts."""
import copy
import hashlib
import json

import pytest
from amphora_contracts_campaigns import ExecutableCampaignV4,ExecutionPlanV4
from amphora_contracts_graph_runtime import GraphLimits
from amphora_contracts_runtime import AttemptBudget
from amphora_evolution_search.composition import GraphWorkBounds


ARTIFACT=dict(kind="artifact",schema_ref=dict(schema_id="fixture.any",version="1",sha256="a"*64),
    representation="fixture",unit="1",media_type="application/json")


def invoke(name,capability="fixture.method"):
    return dict(kind="invoke",node_id=name,tool=dict(capability_id=capability,release="1.0.0",image_sha256="f"*64,contract_version="1"),
        inputs=[dict(port="parameters",source=dict(kind="input",name="candidate"))],timeout_seconds=60,checkpoint=None)


def scope(nodes):
    nodes=[*nodes,dict(kind="finish",node_id="finish",outputs=[dict(port="result",source=dict(kind="input",name="candidate"))])]
    return dict(inputs=[dict(name="candidate",value_type=ARTIFACT)],outputs=[dict(name="result",value_type=ARTIFACT)],
        nodes=nodes,edges=[dict(source=a["node_id"],target=b["node_id"],route="next") for a,b in zip(nodes,nodes[1:])])


def scatter(body,members=32,parallel=8):
    return dict(kind="scatter",node_id="evaluate",collection=dict(kind="input",name="members"),item_input="candidate",
        captures=[],max_members=members,max_parallel=parallel,body=body,result_port="result",policy=dict(kind="all"),
        output=dict(name="result",value_type=dict(kind="collection",item=ARTIFACT,max_items=members,missing_slots=False)))


def loop(body,iterations=3):
    integer=dict(kind="scalar",scalar="integer",unit="1")
    body=copy.deepcopy(body)
    body["inputs"].append(dict(name="i",value_type=integer))
    body["outputs"].append(dict(name="i",value_type=integer))
    body["nodes"][-1]["outputs"].append(dict(port="i",source=dict(kind="input",name="i")))
    return dict(kind="iterate",node_id="batches",state=[dict(name="i",value_type=integer,
        initial=dict(kind="integer",value=0,unit="1"),feedback_port="i")],captures=[],body=body,
        until=dict(kind="constant",value=False),max_iterations=iterations,on_limit="blocked")


def definition(body):
    return ExecutableCampaignV4.model_validate_json(json.dumps(dict(schema_version="4",profile="deterministic-v3",
        campaign_id="work-bounds",revision=1,scope=dict(tenant_id="engineering",project_id="work"),context=[],body=body)))


def test_nested_loop_and_scatter_multiply_total_work_but_not_serial_concurrency():
    graph=definition(scope([invoke("seed","fixture.seed"),loop(scope([scatter(scope([invoke("method")]),members=5,parallel=2)]))]))
    bound=GraphWorkBounds.from_definition(graph)
    assert bound.work.activations==39 and bound.work.scopes==19
    assert {tool.capability_id:count for tool,count in bound.work.calls}=={"fixture.method":15,"fixture.seed":1}
    assert bound.work.queued_upper==3  # seed plus two active child scopes, not15 iterations' methods
    assert bound.check_admission_budget(GraphLimits(max_activations=39),AttemptBudget(limit=48))==48


@pytest.mark.parametrize("batch,overhead",[(1,96),(8,12),(32,3)])
def test_same_method_call_count_has_different_batch_orchestration_cost(batch,overhead):
    body=scope([invoke("prepare","fixture.prepare"),invoke("slice","fixture.slice"),
        scatter(scope([invoke("method")]),members=batch,parallel=min(batch,8)),invoke("cursor","fixture.cursor")])
    work=GraphWorkBounds.from_definition(definition(scope([loop(body,iterations=32//batch)]))).work
    calls={binding.capability_id:count for binding,count in work.calls}
    assert calls["fixture.method"]==32
    assert sum(count for name,count in calls.items() if name!="fixture.method")==overhead


def test_active_attempt_limit_cannot_hide_a_queue_larger_than_the_public_snapshot():
    methods=[invoke("method-"+str(index)) for index in range(9)]
    bound=GraphWorkBounds.from_definition(definition(scope([scatter(scope(methods),members=32,parallel=32)])))
    assert bound.work.invocations==288 and bound.work.queued_upper==288
    with pytest.raises(ValueError,match="queue_budget"):
        bound.check_admission_budget(GraphLimits(),AttemptBudget(limit=1000,max_attempts_per_activation=1))


@pytest.mark.parametrize("limit,budget,reason",[(38,48,"activation_budget"),(39,47,"attempt_budget")])
def test_retry_and_activation_budgets_include_the_whole_authored_tree(limit,budget,reason):
    graph=definition(scope([invoke("seed","fixture.seed"),loop(scope([scatter(scope([invoke("method")]),members=5,parallel=2)]))]))
    with pytest.raises(ValueError,match=reason):GraphWorkBounds.from_definition(graph).check_admission_budget(
        GraphLimits(max_activations=limit),AttemptBudget(limit=budget))


def test_empty_scatter_retains_authored_binding_but_expands_no_child_work():
    work=GraphWorkBounds.from_definition(definition(scope([scatter(scope([invoke("method")]),members=0,parallel=8)]))).work
    assert work.activations==2 and work.scopes==1 and work.queued_upper==0 and work.invocations==0
    assert len(work.calls)==1 and work.calls[0][1]==0


def test_binding_budgets_and_materializations_expand_with_the_scope_tree():
    project=dict(kind="artifact_project",node_id="project",source=dict(kind="input",name="candidate"),path=["items"],
        mode="references",output=dict(name="result",value_type=dict(kind="collection",item=ARTIFACT,max_items=1,missing_slots=False)),
        limits=dict(max_items=1,max_artifacts=2,max_bytes=100,timeout_seconds=30))
    materialize=dict(kind="artifact_materialize",node_id="materialize",fields=[dict(name="ref",mode="references",
        source=dict(kind="input",name="candidate"))],output=dict(name="result",value_type=ARTIFACT),
        limits=dict(max_items=1,max_artifacts=4,max_bytes=200,timeout_seconds=30))
    body=scope([loop(scope([scatter(scope([project,materialize]),members=5,parallel=2)]))])
    work=GraphWorkBounds.from_definition(definition(body)).work
    assert work.invocations==0 and work.bindings.materializations==work.bindings.projections==15
    assert work.bindings.declared_bytes==4500 and work.bindings.declared_artifacts==90


def test_constant_branch_does_not_silently_remove_authored_work_from_preflight():
    body=scope([dict(kind="branch",node_id="choose",predicate=dict(kind="constant",value=False)),invoke("left"),invoke("right")])
    body["edges"]=[dict(source=a,target=b,route=route) for a,b,route in (
        ("choose","left","true"),("choose","right","false"),("left","finish","next"),("right","finish","next"))]
    work=GraphWorkBounds.from_definition(definition(body)).work
    assert work.activations==4 and work.invocations==2 and work.queued_upper==2


def test_nested_large_expansion_rejects_before_safe_integer_overflow():
    body=scope([invoke("method")])
    for _ in range(4):body=scope([scatter(body,members=10000,parallel=1)])
    with pytest.raises(ValueError,match="count_overflow"):GraphWorkBounds.from_definition(definition(body))


def test_unsupported_depth_rejects_even_with_small_declared_iteration_counts():
    body=scope([invoke("method")])
    for _ in range(16):body=scope([loop(body,iterations=1)])
    with pytest.raises(ValueError,match="scope_depth"):GraphWorkBounds.from_definition(definition(body))


@pytest.mark.parametrize("damage",[None,"expected","definition"])
def test_compiled_plan_and_definition_identity_are_checked_before_using_counts(damage):
    graph=definition(scope([invoke("method")]))
    bounds=GraphWorkBounds.from_definition(graph)
    document=dict(profile="amphora-execution-plan-v3",definition=graph.model_dump(mode="json"),
        lock=dict(schema_version="4",compiler_profile="amphora-deterministic-compiler-v3",
            definition_sha256="e"*64 if damage=="definition" else bounds.definition_sha256,tools=[],schemas=[],context=[]),
        scopes=[dict(path=[],order=[node.node_id for node in graph.body.nodes],nodes=[
            dict(node_id=node.node_id,inputs=[],outputs=[]) for node in graph.body.nodes])])
    digest=hashlib.sha256(json.dumps(document,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
    plan=ExecutionPlanV4.model_validate_json(json.dumps(dict(schema_version="4",sha256=digest,document=document)))
    if damage:
        with pytest.raises(ValueError,match="plan_identity" if damage=="expected" else "definition_identity"):
            GraphWorkBounds.from_plan(plan,"e"*64 if damage=="expected" else digest)
    else:
        result=GraphWorkBounds.from_plan(plan,digest)
        assert result.plan_sha256==digest and result.work==bounds.work
