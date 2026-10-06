import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError
from amphora_contracts_evaluation_identity import EvaluationIdentityInput, EvaluationReusePolicy


def example():
    return json.loads((Path(__file__).parent / 'fixtures/input.json').read_bytes())


def test_example_round_trips_and_matches_json_schema():
    value = example()
    model = EvaluationIdentityInput.model_validate_json(json.dumps(value))
    assert model.model_dump(mode='json') == value
    Draft202012Validator(EvaluationIdentityInput.model_json_schema()).validate(value)
    Draft202012Validator(EvaluationReusePolicy.model_json_schema()).validate(value['policy'])


@pytest.mark.parametrize('field', ['material_state', 'inputs'])
def test_unknown_does_not_mean_omitted(field):
    value = example()
    del value['context'][field]
    with pytest.raises(ValidationError):
        EvaluationIdentityInput.model_validate_json(json.dumps(value))
    assert not Draft202012Validator(EvaluationIdentityInput.model_json_schema()).is_valid(value)


def test_extra_authority_is_rejected():
    value = example()
    value['authorized_for_reuse'] = True
    with pytest.raises(ValidationError):
        EvaluationIdentityInput.model_validate_json(json.dumps(value))
