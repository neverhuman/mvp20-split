"""Reference-only intake requests and explicit historical outcome variants."""
import json
from pathlib import Path

import pytest
from amphora_contracts_research import LabIntakeRequest, LabIntakeStatus, LabProfileRef
from jsonschema import Draft202012Validator
from pydantic import ValidationError

EXAMPLES = Path(__file__).absolute().parents[1]/"examples"


@pytest.mark.parametrize("name,model",[
    ("lab-profile-ref",LabProfileRef),("lab-intake-request",LabIntakeRequest),("lab-intake-status",LabIntakeStatus)])
def test_examples_match_both_boundary_schemas(name,model):
    payload = json.loads((EXAMPLES/(name+".json")).read_text())
    assert json.loads(model.model_validate_json(json.dumps(payload)).model_dump_json()) == payload
    for mode in ("validation","serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload)


@pytest.mark.parametrize("outcome",[{"status":"pending"},{"status":"failed","reason":"malformed_report"}])
def test_nonresolved_status_has_no_scientific_verdict(outcome):
    payload = json.loads((EXAMPLES/"lab-intake-status.json").read_text())|{"outcome":outcome}
    assert LabIntakeStatus.model_validate_json(json.dumps(payload)).outcome.status == outcome["status"]
    invalid = payload|{"outcome":outcome|{"eligible":False}}
    with pytest.raises(ValidationError):
        LabIntakeStatus.model_validate_json(json.dumps(invalid))
    assert list(Draft202012Validator(LabIntakeStatus.model_json_schema()).iter_errors(invalid))


@pytest.mark.parametrize("field",["verdict","observations","actor_id","profile_configuration"])
def test_request_cannot_supply_results_actor_or_reviewed_configuration(field):
    payload = json.loads((EXAMPLES/"lab-intake-request.json").read_text())|{field:"caller-input"}
    with pytest.raises(ValidationError):
        LabIntakeRequest.model_validate_json(json.dumps(payload))
    assert list(Draft202012Validator(LabIntakeRequest.model_json_schema()).iter_errors(payload))
