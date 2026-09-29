"""Independent authored wait fixtures and strict isolation from frozen wire-v2."""

import hashlib
import json

import pytest
from amphora_contracts_campaigns import ExecutableCampaign, ExecutableCampaignV3, parse_executable_campaign
from export_schemas import ROOT, publish
from jsonschema import Draft202012Validator
from pydantic import ValidationError

CASES = json.loads((ROOT / "contracts/fixtures/v3/await_cases.json").read_bytes())


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_authored_wait_wire_cases(case):
    raw = json.dumps(case["payload"])
    schema = ExecutableCampaignV3.model_json_schema()
    Draft202012Validator.check_schema(schema)
    assert (not list(Draft202012Validator(schema).iter_errors(case["payload"]))) == case["valid"]
    if case["valid"]:
        definition = parse_executable_campaign(raw)
        assert definition == ExecutableCampaignV3.model_validate_json(raw)
        assert parse_executable_campaign(definition.model_dump_json()) == definition
        Draft202012Validator(ExecutableCampaignV3.model_json_schema(mode="serialization")).validate(
            json.loads(definition.model_dump_json()))
        with pytest.raises(ValidationError):
            ExecutableCampaign.model_validate_json(raw)
    else:
        with pytest.raises(ValidationError):
            parse_executable_campaign(raw)


def test_versioned_publication_and_no_implicit_profile_upgrade(tmp_path):
    assert not publish(tmp_path, version="3")
    assert not publish(tmp_path, check=True, version="3")
    assert not publish(ROOT / "contracts/schemas/v3", check=True, version="3")
    payload = dict(CASES[0]["payload"], schema_version="2", profile="deterministic-v1")
    with pytest.raises(ValidationError):
        parse_executable_campaign(json.dumps(payload))
    for version in ("1", "4"):
        with pytest.raises(ValidationError):
            parse_executable_campaign(json.dumps(dict(CASES[0]["payload"], schema_version=version)))


def test_all_published_predecessor_schema_bytes_remain_identical():
    pins = json.loads((ROOT / "contracts/fixtures/v3/predecessor_schema_pins.json").read_bytes())
    assert len(pins["schemas"]) == 116
    for name, digest in pins["schemas"].items():
        assert hashlib.sha256((ROOT / "contracts/schemas" / name).read_bytes()).hexdigest() == digest, name
