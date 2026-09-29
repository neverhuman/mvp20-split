"""Public wire-v3 inputs compile to exact pinned plans without enabling execution."""

import copy
import hashlib
import json

import pytest
from amphora_campaign_runtime.compiler import CompilationError, ToolCatalog, compile_campaign
from amphora_contracts_campaigns import parse_executable_campaign, parse_execution_plan
from export_schemas import ROOT

CASES = json.loads((ROOT / "contracts/fixtures/v3/await_cases.json").read_bytes())


def test_independently_specified_await_plan_is_exact(compiler_env):
    definition = parse_executable_campaign(json.dumps(CASES[0]["payload"]))
    plan = compile_campaign(definition, ToolCatalog([]), compiler_env.schemas)
    expected = json.loads((ROOT / "contracts/fixtures/v3/await_plan.json").read_bytes())
    assert plan.model_dump(mode="json") == expected


@pytest.mark.parametrize("case", CASES[:3], ids=lambda case: case["name"])
def test_pinned_wait_compiles_without_tool_or_issuer_io(compiler_env, case):
    definition = parse_executable_campaign(json.dumps(case["payload"]))
    plan = compile_campaign(definition, ToolCatalog([]), compiler_env.schemas)
    assert plan.schema_version == "3" and plan.document.lock.schema_version == "3"
    assert plan.document.lock.tools == ()
    assert parse_execution_plan(plan.model_dump_json()) == plan
    encoded = json.dumps(plan.document.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    assert plan.sha256 == hashlib.sha256(encoded).hexdigest()
    bound = [node for scope in plan.document.scopes for node in scope.nodes if node.node_id == "affine"]
    assert len(bound) == 1 and bound[0].inputs[0].name == "subject" and bound[0].outputs[0].name == "result"
    assert bound[0].outputs[0].value_type.kind == "artifact"


@pytest.mark.parametrize("field,code", [("subject", "await_artifact_subject_required"),
                                       ("output", "await_artifact_output_required")])
def test_wait_cannot_accept_untyped_subject_or_output(compiler_env, field, code):
    raw = copy.deepcopy(CASES[0]["payload"])
    node = raw["body"]["nodes"][0]
    if field == "subject":
        node[field] = {"kind": "integer", "value": 1}
    else:
        node[field]["value_type"] = {"kind": "scalar", "scalar": "integer", "unit": "1"}
    with pytest.raises(CompilationError, match=code):
        compile_campaign(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), compiler_env.schemas)


@pytest.mark.parametrize("field,value", [("issuer_id", "other-issuer"), ("purpose", "other-purpose"),
                                       ("expected_revision", "revision-2"), ("timeout_seconds", 61),
                                       ("on_timeout", "abstained")])
def test_wait_expectations_are_part_of_the_plan_identity(compiler_env, field, value):
    raw = copy.deepcopy(CASES[0]["payload"])
    original = compile_campaign(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), compiler_env.schemas)
    raw["body"]["nodes"][0][field] = value
    changed = compile_campaign(parse_executable_campaign(json.dumps(raw)), ToolCatalog([]), compiler_env.schemas)
    assert changed.sha256 != original.sha256
    assert changed.document.lock.definition_sha256 != original.document.lock.definition_sha256
