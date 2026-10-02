import copy
import json
from pathlib import Path

import amphora_contracts_artifacts as contracts
import pytest
from amphora_contracts_commands import CommandEncodingError
from jsonschema import Draft202012Validator
from pydantic import ValidationError

FIXTURE = json.loads((Path(__file__).parent / "fixtures/derivation.json").read_text())
FAMILY = "artifacts.begin_derived_upload"


def test_independent_derived_command_bytes_and_schema():
    raw = FIXTURE["command"]
    Draft202012Validator(contracts.BeginDerivedUpload.model_json_schema()).validate(raw["payload"])
    command = contracts.parse_command(FAMILY, json.dumps(raw))
    assert command.canonical_bytes == FIXTURE["canonical"].encode()
    assert command.sha256 == FIXTURE["sha256"]
    assert command.profile == "amphora-command-v1"
    assert contracts.parse_command(FAMILY, command.canonical_bytes) == command


@pytest.mark.parametrize("count", [0, 129])
def test_input_bounds(count):
    raw = copy.deepcopy(FIXTURE["command"])
    raw["payload"]["declaration"]["inputs"] *= count
    with pytest.raises(CommandEncodingError, match="schema_invalid"):
        contracts.parse_command(FAMILY, json.dumps(raw))


def test_maximum_inputs_and_exact_scope():
    raw = copy.deepcopy(FIXTURE["command"])
    original = raw["payload"]["declaration"]["inputs"][0]
    inputs = [{**original, "artifact_id": f"input-{index}"} for index in range(128)]
    raw["payload"]["declaration"]["inputs"] = inputs
    contracts.parse_command(FAMILY, json.dumps(raw))
    inputs[-1]["scope"] = {"tenant_id": "foreign", "project_id": "demo"}
    with pytest.raises(CommandEncodingError, match="scope_mismatch"):
        contracts.parse_command(FAMILY, json.dumps(raw))


@pytest.mark.parametrize("field,value", [("rights_override", True), ("code", "eval(x)"), ("schema_version", "2")])
def test_declarations_do_not_install_authority_or_code(field, value):
    raw = copy.deepcopy(FIXTURE["command"])
    raw["payload"]["declaration"][field] = value
    with pytest.raises(CommandEncodingError, match="schema_invalid"):
        contracts.parse_command(FAMILY, json.dumps(raw))


def test_derived_observation_does_not_widen_legacy_outcome():
    command = contracts.parse_command(FAMILY, json.dumps(FIXTURE["command"]))
    payload = json.loads(command.canonical_bytes)["payload"]
    upload = {"upload_id": "upload-1", "scope": command.identity.scope.model_dump(), "content": payload["content"]}
    value = {"identity": command.identity.model_dump(), "operation_id": "op-1", "request_sha256": command.sha256,
             "outcome": {"status": "derived_uploaded", "receipt": {"upload": upload, "declaration": payload["declaration"]}}}
    contracts.DerivedUploadObservation.model_validate_json(json.dumps(value))
    with pytest.raises(ValidationError):
        contracts.PublicationObservation.model_validate_json(json.dumps(value))
    with pytest.raises(CommandEncodingError, match="schema_invalid"):
        contracts.parse_command("artifacts.begin_upload", command.canonical_bytes)
    wrong_family = copy.deepcopy(FIXTURE["command"])
    wrong_family["identity"]["command_family"] = "artifacts.begin_upload"
    with pytest.raises(CommandEncodingError, match="family_mismatch"):
        contracts.parse_command(FAMILY, json.dumps(wrong_family))
