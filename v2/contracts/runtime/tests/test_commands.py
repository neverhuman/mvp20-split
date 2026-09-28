import copy
import json
from pathlib import Path

import amphora_contracts_runtime as contracts
import pytest
from amphora_contracts_commands import CommandEncodingError
from jsonschema import Draft202012Validator

CASES = json.loads((Path(__file__).parent / "fixtures/commands.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["family"])
def test_command_schema_roundtrip_and_family_binding(case):
    model = getattr(contracts, case["model"])
    schema = model.model_json_schema(mode="validation")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(case["command"]["payload"])
    result = contracts.parse_command(case["family"], json.dumps(case["command"]))
    assert contracts.parse_command(case["family"], result.canonical_bytes) == result
    changed = copy.deepcopy(case["command"])
    changed["identity"]["command_family"] = "wrong.operation"
    with pytest.raises(CommandEncodingError, match="family_mismatch"):
        contracts.parse_command(case["family"], json.dumps(changed))
    changed = copy.deepcopy(case["command"])
    changed["payload"]["undeclared_authority"] = True
    assert list(Draft202012Validator(schema).iter_errors(changed["payload"]))
    with pytest.raises(CommandEncodingError, match="schema_invalid"):
        contracts.parse_command(case["family"], json.dumps(changed))
    changed = copy.deepcopy(case["command"])
    changed["identity"]["schema_version"] = "2"
    with pytest.raises(CommandEncodingError, match="schema_invalid"):
        contracts.parse_command(case["family"], json.dumps(changed))


def test_unknown_operation_is_not_dynamic_dispatch():
    with pytest.raises(CommandEncodingError, match="unknown_family"):
        contracts.parse_command("arbitrary.execute", "{}")
