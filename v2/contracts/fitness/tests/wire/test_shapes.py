import json
from pathlib import Path

import pytest
from amphora_contracts_fitness import FitnessProfile, FitnessRequest
from jsonschema import Draft202012Validator
from pydantic import ValidationError


@pytest.mark.parametrize('name,model',[('profile',FitnessProfile),('request',FitnessRequest)])
def test_examples_roundtrip_and_have_schema_parity(name,model):
    data = json.loads((Path(__file__).parent/'fixtures'/(name+'.json')).read_bytes())
    assert model.model_validate_json(json.dumps(data)).model_dump(mode='json') == data
    Draft202012Validator(model.model_json_schema()).validate(data)
    data['trusted'] = True
    with pytest.raises(ValidationError):
        model.model_validate_json(json.dumps(data))
    assert not Draft202012Validator(model.model_json_schema()).is_valid(data)


def test_submitted_verdict_cannot_replace_references():
    data = json.loads((Path(__file__).parent/'fixtures/request.json').read_bytes())
    data['eligibility'] = {'disposition':'eligible'}
    with pytest.raises(ValidationError):
        FitnessRequest.model_validate_json(json.dumps(data))
