import json

import pytest
from amphora_contracts_evaluation_reuse import ProducerRef, ReuseProjection, ReuseRequest
from jsonschema import Draft202012Validator
from pydantic import ValidationError


def test_producer_selection_is_reference_only_and_schema_parity():
    raw={'scope':{'tenant_id':'fixture','project_id':'fixture'},'run_id':'run','completion_id':'complete'}
    record=ProducerRef.model_validate_json(json.dumps(raw))
    Draft202012Validator(ProducerRef.model_json_schema()).validate(raw)
    assert record.model_dump(mode='json')==raw
    raw['invocation']={}
    with pytest.raises(ValidationError):ProducerRef.model_validate_json(json.dumps(raw))


def test_request_selects_owner_records_and_projection_has_narrow_authority():
    fields=ReuseRequest.model_fields
    assert set(fields)=={'wire_version','reuse_id','profile','source','target','evaluation','eligibility','synthesis'}
    schema=ReuseProjection.model_json_schema()
    assert schema['properties']['authority']['const']=='synthetic_reuse_decision'
    assert schema['properties']['status']['enum']==['permitted','miss','ineligible']
