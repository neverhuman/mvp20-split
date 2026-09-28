"""Positive edge cases prevent rejection-only tests from collapsing useful graph behavior."""

import copy

import pytest
from amphora_campaign_runtime.compiler import CompilationError, compile_campaign

from .conftest import definition


def test_parallel_roots_can_feed_an_ordinary_and_successor(compiler_env):
    env = compiler_env
    raw = env.raw[0]
    body = raw["body"]
    beta = copy.deepcopy(body["nodes"][0])
    beta["node_id"] = "beta"
    body["nodes"].append(beta)
    body["edges"].append({"source": "beta", "target": "finish", "route": "next"})
    other = copy.deepcopy(body["outputs"][0])
    other["name"] = "other"
    body["outputs"].append(other)
    body["nodes"][1]["outputs"].append({"port": "other", "source": {"kind": "output", "node_id": "beta", "port": "result"}})
    plan = compile_campaign(definition(raw), env.tools, env.schemas)
    assert plan.document.scopes[0].order == ("affine", "beta", "finish")


def test_required_all_join_preserves_availability_but_partial_does_not(compiler_env):
    env = compiler_env
    raw = env.raw[1]
    body = raw["body"]
    del body["nodes"][0]
    body["edges"] = body["edges"][2:]
    extra = copy.deepcopy(env.raw[0]["body"]["outputs"][0])
    extra["name"] = "left"
    body["outputs"].append(extra)
    body["nodes"][-1]["outputs"].append({"port": "left", "source": {"kind": "output", "node_id": "left", "port": "result"}})
    compile_campaign(definition(raw), env.tools, env.schemas)
    join = body["nodes"][2]
    join["policy"] = {"kind": "partial", "minimum": 1, "close": "all_terminal"}
    join["output"]["value_type"]["missing_slots"] = True
    body["outputs"][0]["value_type"]["missing_slots"] = True
    with pytest.raises(CompilationError, match="unavailable_output"):
        compile_campaign(definition(raw), env.tools, env.schemas)


def test_zero_scatter_and_explicit_capture(compiler_env):
    env = compiler_env
    raw = env.raw[2]
    raw["body"]["inputs"][0]["value_type"]["max_items"] = 0
    scatter = raw["body"]["nodes"][0]
    scatter["max_members"] = 0
    scalar = {"kind": "scalar", "scalar": "integer", "unit": "1"}
    scatter["body"]["inputs"].append({"name": "seed", "value_type": scalar})
    scatter["captures"] = [{"port": "seed", "source": {"kind": "integer", "value": 7, "unit": "1"}}]
    plan = compile_campaign(definition(raw), env.tools, env.schemas)
    assert plan.document.definition.body.nodes[0].max_members == 0


def test_artifact_constant_scope_and_schema_projection_predicate(compiler_env):
    env = compiler_env
    raw = env.raw[1]
    artifact_type = raw["body"]["inputs"][0]["value_type"]
    constant = {"kind": "artifact", "representation": artifact_type["representation"], "unit": "1",
                "artifact": {"artifact_id": "immutable-input", "scope": raw["scope"], "sha256": "a" * 64,
                             "media_type": "application/json", "schema_ref": artifact_type["schema_ref"], "size_bytes": 100}}
    compare = {"kind": "compare", "left": {"source": constant, "path": ["values", 0],
               "value_type": {"kind": "scalar", "scalar": "number", "unit": "1"}},
               "operator": "ge", "right": {"kind": "number", "value": 0.0, "unit": "1"}}
    raw["body"]["nodes"][0]["predicate"] = {"kind": "all", "predicates": [
        compare, {"kind": "any", "predicates": [{"kind": "constant", "value": True},
        {"kind": "not", "predicate": {"kind": "constant", "value": False}}]}]}
    compile_campaign(definition(raw), env.tools, env.schemas)
    constant["artifact"]["scope"] = {"tenant_id": "wrong", "project_id": "wrong"}
    with pytest.raises(CompilationError, match="artifact_scope_mismatch"):
        compile_campaign(definition(raw), env.tools, env.schemas)
