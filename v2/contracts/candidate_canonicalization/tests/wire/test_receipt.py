import json

import pytest
from amphora_contracts_candidate_canonicalization import CanonicalCandidate
from jsonschema import Draft202012Validator
from pydantic import ValidationError


def example():
    pin={'schema_id':'fixture.pin','version':'1','sha256':'a'*64}
    return {'wire_version':'1','authority':'synthetic_encoding','scope':{'tenant_id':'fixture','project_id':'canonical'},
        'kind':'polymer','semantic_profile':pin,'equivalence_profile':pin,'source_sha256':'b'*64,'canonical_sha256':'c'*64}


def test_receipt_wire_schema_parity():
    value=example()
    assert CanonicalCandidate.model_validate_json(json.dumps(value)).model_dump(mode='json')==value
    Draft202012Validator(CanonicalCandidate.model_json_schema()).validate(value)


@pytest.mark.parametrize('field,value',[('authority','scientific'),('source_sha256','bad'),('kind','universal'),('authorized',True)])
def test_receipt_cannot_promote_or_widen_its_scope(field,value):
    data=example();data[field]=value
    with pytest.raises(ValidationError):CanonicalCandidate.model_validate_json(json.dumps(data))
    assert not Draft202012Validator(CanonicalCandidate.model_json_schema()).is_valid(data)
