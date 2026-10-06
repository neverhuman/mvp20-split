"""Graph composition, policy routing and deterministic compile identity; no SQL."""

import copy
import json

import pytest
from amphora_campaign_runtime.compiler import CompilationError, compile_campaign
from amphora_contracts_campaigns import parse_executable_campaign

from .catalog import catalog
from .definition import campaign

SCOPE = {"tenant_id": "numeric-search", "project_id": "compiler"}


def compile_raw(raw):
    _, tools, schemas = catalog()
    return compile_campaign(parse_executable_campaign(json.dumps(raw)), tools, schemas)


@pytest.mark.parametrize("generations", [0, 1, 2, 10000])
def test_bounded_graph_compiles_with_explicit_policy_and_stop(generations):
    raw = campaign(SCOPE, catalog()[0], generations)
    plan = compile_raw(raw)
    assert len(plan.document.scopes) == (4 if generations else 2)
    assert compile_raw(copy.deepcopy(raw)).sha256 == plan.sha256
    assert {port.name for port in plan.document.definition.body.inputs} == {"specification", "policy"}
    if generations:
        loop = next(node for node in plan.document.definition.body.nodes if node.kind == "iterate")
        assert loop.until.right.value == "stopped"
        assert loop.on_limit == "blocked"
        assert loop.max_iterations == generations


@pytest.mark.parametrize("fault", ["missing_capture", "missing_policy", "wrong_policy", "no_missing_slots", "small_members"])
def test_broken_composition_is_rejected(fault):
    raw = campaign(SCOPE, catalog()[0], 1)
    scatter = next(node for node in raw["body"]["nodes"] if node["kind"] == "scatter")
    evaluator = scatter["body"]["nodes"][0]
    if fault == "missing_capture":
        scatter["captures"] = []
    elif fault == "missing_policy":
        evaluator["inputs"].pop()
    elif fault == "wrong_policy":
        evaluator["inputs"][1]["source"]["name"] = "candidate"
    elif fault == "no_missing_slots":
        scatter["output"]["value_type"]["missing_slots"] = False
    else:
        scatter["max_members"] = 127
    with pytest.raises(CompilationError):
        compile_raw(raw)


def test_bounds_and_capture_changes_change_plan_identity():
    raw = campaign(SCOPE, catalog()[0], 2)
    baseline = compile_raw(raw).sha256
    assert compile_raw(campaign(SCOPE, catalog()[0], 1)).sha256 != baseline
    raw["body"]["nodes"][0]["timeout_seconds"] = 59
    assert compile_raw(raw).sha256 != baseline


@pytest.mark.parametrize("value", [-1, 10001, True, 1.0])
def test_invalid_iteration_limit(value):
    with pytest.raises(ValueError, match="generation_count"):
        campaign(SCOPE, catalog()[0], value)
