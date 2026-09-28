"""Explicit wire-v2 compatibility, independently specified shapes and legacy isolation."""

import json

import pytest
from amphora_contracts_campaigns import CampaignDefinition, ExecutableCampaign
from export_schemas import MODELS_V2, ROOT, artifacts, publish
from jsonschema import Draft202012Validator
from pydantic import ValidationError

CASES = json.loads((ROOT / "contracts/fixtures/v2/executable_cases.json").read_bytes())


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_explicit_wire_cases(case):
    model = MODELS_V2[case["model"]]
    schema = model.model_json_schema(mode="validation")
    Draft202012Validator.check_schema(schema)
    valid = not list(Draft202012Validator(schema).iter_errors(case["payload"]))
    assert valid == case["valid"]
    raw = json.dumps(case["payload"])
    if case["valid"]:
        parsed = model.model_validate_json(raw)
        assert model.model_validate_json(parsed.model_dump_json()) == parsed
        Draft202012Validator(model.model_json_schema(mode="serialization")).validate(json.loads(parsed.model_dump_json()))
    else:
        with pytest.raises(ValidationError):
            model.model_validate_json(raw)


def test_executable_and_legacy_roots_never_implicitly_convert():
    with pytest.raises(ValidationError):
        CampaignDefinition.model_validate_json(json.dumps(CASES[0]["payload"]))
    legacy = {"schema_version": "1", "campaign_id": "legacy", "revision": 1,
        "scope": {"tenant_id": "t", "project_id": "p"},
        "body": {"nodes": [{"kind": "finish", "node_id": "done"}], "edges": []}}
    assert CampaignDefinition.model_validate_json(json.dumps(legacy)).schema_version == "1"
    with pytest.raises(ValidationError):
        ExecutableCampaign.model_validate_json(json.dumps(legacy))


def test_two_versioned_bundles_have_separate_identities_and_no_publication_drift(tmp_path):
    for version in ("1", "2"):
        directory = tmp_path / version
        assert not publish(directory, version=version)
        assert not publish(directory, check=True, version=version)
        assert artifacts(version) == {p.name: p.read_bytes() for p in directory.glob("*.json")}
        schema = json.loads((directory / "campaigns.definition.validation.json").read_bytes())
        assert schema["$id"] == "urn:amphora:campaigns.definition:" + version + ":validation"
    assert not publish(ROOT / "contracts/schemas/v1", check=True)
    assert not publish(ROOT / "contracts/schemas/v2", check=True, version="2")


def test_wire_definition_is_frozen_and_binds_exact_tool_schema():
    value = ExecutableCampaign.model_validate_json(json.dumps(CASES[0]["payload"]))
    assert isinstance(value.body.nodes, tuple) and isinstance(value.body.inputs, tuple)
    with pytest.raises(ValidationError):
        value.revision = 2
    with pytest.raises(ValidationError):
        value.body.nodes[0].tool.release = "latest"
