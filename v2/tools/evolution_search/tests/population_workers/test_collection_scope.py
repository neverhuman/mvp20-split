"""Repeated names do not let previous loop occurrences enter current collection."""
from types import SimpleNamespace

import pytest
from amphora_evolution_search.population_workers.collection_scope import CollectionScope

from .test_selection_cut import counter_case


def scope_case(loop=True):
    inspection,capture,execution=counter_case(loop=loop,loop_index=1)
    calls=[]
    def binding(node):
        calls.append(node.activation_id)
        return "declared-primary-method"
    plan=SimpleNamespace(execution=execution,scope_path=("generation","evaluate") if loop else ("evaluate",),binding=binding)
    scope=CollectionScope.load(capture,plan,inspection.attempt.invocation)
    node=next(node for node in capture.nodes if node.path.node_id=="source")
    return scope,node,capture,plan,inspection.attempt.invocation,calls


def test_only_current_occurrence_reaches_method_attribution():
    scope,node,_,_,_,calls=scope_case()
    previous=node.model_copy(update={"path":node.path.model_copy(update={"occurrences":
        (node.path.occurrences[0].model_copy(update={"index":0}),)})})
    assert scope.binding(previous) is None and calls==[]
    assert scope.binding(node)=="declared-primary-method" and calls==[node.activation_id]


def test_root_collection_preserves_method_scope_filtering():
    scope,node,_,_,_,calls=scope_case(False)
    assert scope.binding(node)=="declared-primary-method" and len(calls)==1


@pytest.mark.parametrize("change",[
    {"index":0}, {"node_id":"other-generation"},
])
def test_occurrence_identity_includes_every_frame_field(change):
    scope,node,_,_,_,calls=scope_case()
    frame=node.path.occurrences[0].model_copy(update=change)
    other=node.model_copy(update={"path":node.path.model_copy(update={"occurrences":(frame,)})})
    assert scope.binding(other) is None
    assert calls==[]


def test_captured_plan_must_match_the_supplied_execution_plan():
    _,_,capture,plan,invocation,_=scope_case()
    capture=SimpleNamespace(nodes=capture.nodes,snapshot=capture.snapshot.model_copy(update={
        "cut":capture.snapshot.cut.model_copy(update={"plan_sha256":"a"*64})}))
    with pytest.raises(ValueError,match="scope_plan"):
        CollectionScope.load(capture,plan,invocation)


def test_scatter_membership_is_part_of_ancestor_identity():
    from amphora_contracts_graph_runtime import GraphNodeViewV3
    scope,node,_,_,_,calls=scope_case()
    raw=node.model_dump(mode="json")
    raw["path"]["occurrences"]=[dict(kind="scatter",node_id="outer",index=1,membership_sha256="b"*64)]
    import json
    frame=GraphNodeViewV3.model_validate_json(json.dumps(raw)).path.occurrences[0]
    caller=scope.caller.model_copy(update={"path":scope.caller.path.model_copy(update={"occurrences":(frame,)})})
    scope=CollectionScope(scope.plan,caller)
    current=node.model_copy(update={"path":node.path.model_copy(update={"occurrences":(frame,)})})
    other=current.model_copy(update={"path":current.path.model_copy(update={"occurrences":(
        frame.model_copy(update={"membership_sha256":"c"*64}),)})})
    assert scope.binding(other) is None and calls==[]
    assert scope.binding(current)=="declared-primary-method"


@pytest.mark.parametrize("changed_ancestor",[0,1])
def test_nested_loops_require_both_ancestor_occurrences(changed_ancestor):
    scope,node,_,_,_,calls=scope_case()
    outer=node.path.occurrences[0]
    inner=outer.model_copy(update={"node_id":"inner-generation"})
    ancestors=(outer,inner)
    caller=scope.caller.model_copy(update={"path":scope.caller.path.model_copy(update={"occurrences":ancestors})})
    scope=CollectionScope(scope.plan,caller)
    current=node.model_copy(update={"path":node.path.model_copy(update={"occurrences":ancestors})})
    other=list(ancestors)
    other[changed_ancestor]=other[changed_ancestor].model_copy(update={"index":0})
    previous=current.model_copy(update={"path":current.path.model_copy(update={"occurrences":tuple(other)})})
    assert scope.binding(previous) is None and calls==[]
    assert scope.binding(current)=="declared-primary-method"


@pytest.mark.parametrize("change,reason",[("missing","scope_caller"),("tool","scope_tool"),("path","scope_path")])
def test_caller_must_be_current_and_bound_to_its_admitted_scope(change,reason):
    _,_,capture,plan,invocation,_=scope_case()
    if change=="missing": invocation.activation_id="not-the-caller"
    if change=="tool": invocation.tool=invocation.tool.model_copy(update={"release":"99.0.0"})
    if change=="path": plan.scope_path=("other-loop","evaluate")
    with pytest.raises(ValueError,match=reason): CollectionScope.load(capture,plan,invocation)
