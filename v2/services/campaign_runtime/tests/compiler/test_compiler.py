"""Behavioral proof of pure compilation; manual wire fixtures predate the implementation."""

import copy
import json

import pytest
from amphora_campaign_runtime.compiler import ActivationAddress, CompilationError, compile_campaign
from amphora_contracts_campaigns import ActivationPath
from pydantic import ValidationError

from .conftest import definition


@pytest.mark.parametrize("index", range(4))
def test_scoped_examples_compile(compiler_env, index):
    env = compiler_env
    result = compile_campaign(definition(env.raw[index]), env.tools, env.schemas)
    assert result.document.definition.campaign_id == env.raw[index]["campaign_id"]
    assert len(result.document.scopes) == (2 if index in (2, 3) else 1)
    assert result == compile_campaign(definition(env.raw[index]), env.tools, env.schemas)
    with pytest.raises(ValidationError):
        result.sha256 = "0" * 64


def test_matches_preexisting_manual_plan(compiler_env):
    env = compiler_env
    result = compile_campaign(definition(env.raw[0]), env.tools, env.schemas)
    assert result.model_dump(mode="json") == env.expected


@pytest.mark.parametrize("index", range(4))
def test_irrelevant_authored_order_does_not_change_plan(compiler_env, index):
    env = compiler_env
    raw = env.raw[index]
    before = compile_campaign(definition(raw), env.tools, env.schemas)
    altered = copy.deepcopy(raw)

    def shuffle(body):
        for key in ("nodes", "edges", "inputs", "outputs"):
            body.get(key, []).reverse()
        for node in body["nodes"]:
            for key in ("inputs", "outputs", "captures", "state"):
                node.get(key, []).reverse()
            if "body" in node:
                shuffle(node["body"])

    shuffle(altered["body"])
    assert compile_campaign(definition(altered), env.tools, env.schemas) == before


def test_branch_output_cannot_bypass_join(compiler_env):
    env = compiler_env
    raw = env.raw[1]
    body = raw["body"]
    finish = next(node for node in body["nodes"] if node["kind"] == "finish")
    left = next(node for node in body["nodes"] if node["kind"] == "invoke")
    body["outputs"][0]["value_type"] = env.raw[0]["body"]["outputs"][0]["value_type"]
    finish["outputs"][0]["source"] = {"kind": "output", "node_id": left["node_id"], "port": "result"}
    with pytest.raises(CompilationError, match="unavailable_output"):
        compile_campaign(definition(raw), env.tools, env.schemas)


def test_partial_join_requires_missing_slots_and_deadline_policy(compiler_env):
    env = compiler_env
    raw = env.raw[1]
    join = next(node for node in raw["body"]["nodes"] if node["kind"] == "join")
    join["policy"] = {"kind": "partial", "minimum": 1, "close": "deadline", "deadline_seconds": 5}
    with pytest.raises(CompilationError, match="partial_missing_slots_required"):
        compile_campaign(definition(raw), env.tools, env.schemas)
    join["output"]["value_type"]["missing_slots"] = True
    raw["body"]["outputs"][0]["value_type"]["missing_slots"] = True
    compile_campaign(definition(raw), env.tools, env.schemas)
    join["policy"]["close"] = "all_terminal"
    with pytest.raises(CompilationError, match="partial_deadline_policy"):
        compile_campaign(definition(raw), env.tools, env.schemas)


def test_loop_address_is_plan_bound_and_validated(compiler_env):
    env = compiler_env
    plan = compile_campaign(definition(env.raw[3]), env.tools, env.schemas)
    loop = next(node for node in plan.document.definition.body.nodes if node.kind == "iterate")
    path = {"schema_version": "2", "node_id": loop.body.nodes[0].node_id,
            "occurrences": [{"kind": "loop", "node_id": loop.node_id, "index": 0}]}
    first = ActivationAddress.for_plan(plan, ActivationPath.model_validate_json(json.dumps(path)))
    path["occurrences"][0]["index"] = 1
    second = ActivationAddress.for_plan(plan, ActivationPath.model_validate_json(json.dumps(path)))
    assert first.key != second.key
    path["occurrences"][0]["index"] = loop.max_iterations
    with pytest.raises(CompilationError, match="occurrence_bound"):
        ActivationAddress.for_plan(plan, ActivationPath.model_validate_json(json.dumps(path)))
