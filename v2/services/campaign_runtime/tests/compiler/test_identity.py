"""Identity changes only at semantic boundaries; addresses include frozen membership."""

import copy
import json

import pytest
from amphora_campaign_runtime.compiler import ActivationAddress, CompilationError, compile_campaign
from amphora_contracts_campaigns import ActivationPath

from .conftest import definition


@pytest.mark.parametrize("index,orders", [
    (0, {(): ("affine", "finish")}),
    (1, {(): ("choose", "left", "right", "collect", "finish")}),
    (2, {(): ("batch", "finish"), ("batch",): ("map", "finish")}),
    (3, {(): ("loop", "finish"), ("loop",): ("finish",)}),
])
def test_manually_specified_scope_orders(compiler_env, index, orders):
    env = compiler_env
    plan = compile_campaign(definition(env.raw[index]), env.tools, env.schemas)
    assert {scope.path: scope.order for scope in plan.document.scopes} == orders
    assert len(plan.document.lock.tools) == (0 if index == 3 else 1)
    assert len(plan.document.lock.schemas) == (0 if index == 3 else 2)


def test_ordered_members_and_policy_context_change_identity(compiler_env):
    env = compiler_env
    raw = env.raw[1]
    before = compile_campaign(definition(raw), env.tools, env.schemas)
    raw["body"]["nodes"][3]["members"].reverse()
    after = compile_campaign(definition(raw), env.tools, env.schemas)
    assert before.sha256 != after.sha256
    assert before.document.lock.definition_sha256 != after.document.lock.definition_sha256
    raw["context"] = [{"kind": "policy", "identity": "strict", "revision": "1", "sha256": "a" * 64},
                      {"kind": "knowledge", "identity": "synthetic", "revision": "7", "sha256": "b" * 64}]
    pinned = compile_campaign(definition(raw), env.tools, env.schemas)
    assert pinned.sha256 != after.sha256
    raw["context"].reverse()
    assert compile_campaign(definition(raw), env.tools, env.schemas) == pinned
    raw["context"].append(copy.deepcopy(raw["context"][0]))
    with pytest.raises(CompilationError, match="duplicate_context_pin"):
        compile_campaign(definition(raw), env.tools, env.schemas)


def test_scatter_occurrence_membership_and_plan_are_part_of_identity(compiler_env):
    env = compiler_env
    raw = env.raw[2]
    plan = compile_campaign(definition(raw), env.tools, env.schemas)

    def address(index=0, membership="a", source=plan):
        path = ActivationPath.model_validate_json(json.dumps({"schema_version": "2", "node_id": "map", "occurrences": [
            {"kind": "scatter", "node_id": "batch", "index": index, "membership_sha256": membership * 64}]}))
        return ActivationAddress.for_plan(source, path).key

    raw["revision"] += 1
    successor = compile_campaign(definition(raw), env.tools, env.schemas)
    assert len({address(), address(1), address(membership="b"), address(source=successor)}) == 4
    with pytest.raises(CompilationError, match="occurrence_bound"):
        address(3)


@pytest.mark.parametrize("node_id,occurrences,code", [
    ("absent", [], "unknown_activation_node"),
    ("map", [{"kind": "loop", "node_id": "absent", "index": 0}], "unknown_occurrence_node"),
    ("map", [{"kind": "loop", "node_id": "batch", "index": 0}], "occurrence_kind_mismatch"),
])
def test_invalid_scoped_addresses(compiler_env, node_id, occurrences, code):
    env = compiler_env
    plan = compile_campaign(definition(env.raw[2]), env.tools, env.schemas)
    path = ActivationPath.model_validate_json(json.dumps({"schema_version": "2", "node_id": node_id, "occurrences": occurrences}))
    with pytest.raises(CompilationError, match=code):
        ActivationAddress.for_plan(plan, path)


def test_predicate_and_scope_depth_limits_are_explicit(compiler_env):
    env = compiler_env
    raw = env.raw[1]
    predicate = {"kind": "constant", "value": True}
    for _ in range(17):
        predicate = {"kind": "not", "predicate": predicate}
    raw["body"]["nodes"][0]["predicate"] = predicate
    with pytest.raises(CompilationError, match="predicate_complexity_limit"):
        compile_campaign(definition(raw), env.tools, env.schemas)
    raw = env.raw[3]
    body = copy.deepcopy(raw["body"]["nodes"][0]["body"])
    for _ in range(17):
        loop = copy.deepcopy(raw["body"]["nodes"][0])
        loop["body"] = body
        loop["state"][0]["initial"] = {"kind": "input", "name": "counter"}
        body = {"inputs": copy.deepcopy(body["inputs"]), "outputs": copy.deepcopy(body["outputs"]),
                "nodes": [loop, copy.deepcopy(raw["body"]["nodes"][1])], "edges": copy.deepcopy(raw["body"]["edges"])}
    raw["body"] = body
    with pytest.raises(CompilationError, match="graph_complexity_limit"):
        compile_campaign(definition(raw), env.tools, env.schemas)
