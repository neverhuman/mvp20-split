import json

import pytest
from amphora_contracts_synthetic_evaluation import SyntheticEvaluationReceipt
from jsonschema import Draft202012Validator
from pydantic import ValidationError


def receipt():
    pin = {'schema_id': 'fixture', 'version': '1', 'sha256': 'a' * 64}
    return {'wire_version': '1', 'authority': 'synthetic_evaluation',
        'scope': {'tenant_id': 'fixture', 'project_id': 'fixture'},
        'input_sha256': 'a' * 64, 'canonical_sha256': 'b' * 64,
        'method': {'evaluator': {'capability_id': 'synthetic.digest-score', 'release': '0.1.0',
             'image_sha256': 'c' * 64, 'contract_version': '1'}, 'method': pin, 'applicability': pin},
        'objective_id': 'synthetic-digest-score', 'unit': '1', 'value': 1}


def test_shape_preserves_narrow_authority():
    raw = receipt()
    record = SyntheticEvaluationReceipt.model_validate_json(json.dumps(raw))
    Draft202012Validator(SyntheticEvaluationReceipt.model_json_schema()).validate(raw)
    assert record.model_dump(mode='json') == raw


@pytest.mark.parametrize('field,value', [('authority','scientific'),('value',-1),('value',16777216),('value',True),('value',1.5),('unit','kg'),('reuse_permission',True)])
def test_no_coercion_broad_authority_or_out_of_range(field, value):
    raw = receipt(); raw[field] = value
    with pytest.raises(ValidationError):
        SyntheticEvaluationReceipt.model_validate_json(json.dumps(raw))
