"""Explicit authored conversion fixtures, portable schemas and frozen predecessor bytes."""

import hashlib
import json

import pytest
from amphora_contracts_campaigns import (
    BindingPrimitiveDescriptor,
    ExecutableCampaignV3,
    ExecutableCampaignV4,
    parse_executable_campaign,
)
from export_schemas import ROOT, publish
from jsonschema import Draft202012Validator
from pydantic import ValidationError

FOLDER = ROOT / "contracts/fixtures/v4"
CASES = json.loads((FOLDER / "binding_cases.json").read_bytes())


@pytest.mark.parametrize("case", CASES, ids=lambda item: item["name"])
def test_explicit_wire_conversions(case):
    schema = ExecutableCampaignV4.model_json_schema()
    validator = Draft202012Validator(schema)
    if case["valid"]:
        parsed = parse_executable_campaign(json.dumps(case["payload"]))
        assert parsed.schema_version == "4"
        assert not list(validator.iter_errors(case["payload"]))
        with pytest.raises(ValidationError):
            ExecutableCampaignV3.model_validate_json(json.dumps(case["payload"]))
    else:
        assert list(validator.iter_errors(case["payload"]))
        with pytest.raises(ValidationError):
            parse_executable_campaign(json.dumps(case["payload"]))


def test_all_published_predecessor_schema_bytes_remain_pinned():
    pins = json.loads((FOLDER / "predecessor_schema_pins.json").read_bytes())["schemas"]
    assert len(pins) == 134
    for name, expected in pins.items():
        assert hashlib.sha256((ROOT / "contracts/schemas" / name).read_bytes()).hexdigest() == expected
    assert publish(ROOT / "contracts/schemas/v4", check=True, version="4") == []


def test_builtin_descriptors_expose_only_typed_conversion_authority():
    raw = json.loads((FOLDER / "binding_primitives.json").read_bytes())
    descriptors = [BindingPrimitiveDescriptor.model_validate_json(json.dumps(value)) for value in raw]
    assert [item.kind for item in descriptors] == ["artifact_project", "artifact_materialize"]
    assert all(item.scientific_authority == "none" and item.owner == "campaign_runtime" for item in descriptors)
