"""Pending execution and completed unresolved science remain distinct wire states."""
import json
from pathlib import Path

import pytest
from amphora_contracts_research import InterpretationSelection, InterpretationStatus
from jsonschema import Draft202012Validator
from pydantic import ValidationError

EXAMPLES = Path(__file__).absolute().parents[1]/"examples"


@pytest.mark.parametrize("name,model",[("interpretation-selection",InterpretationSelection),("interpretation-status",InterpretationStatus)])
def test_examples_roundtrip_and_both_schema_modes(name,model):
    payload = json.loads((EXAMPLES/(name+".json")).read_text())
    assert json.loads(model.model_validate_json(json.dumps(payload)).model_dump_json()) == payload
    for mode in ("validation","serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload)


def test_pending_has_no_projection_and_normalization_completion_is_typed():
    payload = json.loads((EXAMPLES/"interpretation-status.json").read_text())
    pending = payload|{"outcome":{"status":"pending"}}
    assert InterpretationStatus.model_validate_json(json.dumps(pending)).outcome.status == "pending"
    invalid = payload|{"outcome":{**payload["outcome"],"status":"pending"}}
    with pytest.raises(ValidationError):
        InterpretationStatus.model_validate_json(json.dumps(invalid))
    assert list(Draft202012Validator(InterpretationStatus.model_json_schema()).iter_errors(invalid))
    payload["request"] = json.loads((EXAMPLES/"normalize-observation-request.json").read_text())
    payload["outcome"]["projection"] = json.loads((EXAMPLES/"normalization-projection.json").read_text())
    assert InterpretationStatus.model_validate_json(json.dumps(payload)).outcome.projection.kind == "normalization"
    Draft202012Validator(InterpretationStatus.model_json_schema()).validate(payload)


@pytest.mark.parametrize("field,value",[("runtime_accepted",True),("scientifically_valid",True)])
def test_status_cannot_claim_execution_or_scientific_acceptance(field,value):
    payload = json.loads((EXAMPLES/"interpretation-status.json").read_text())|{field:value}
    with pytest.raises(ValidationError):
        InterpretationStatus.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(InterpretationStatus.model_json_schema()).iter_errors(payload))
