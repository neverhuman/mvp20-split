import hashlib
import json

import pytest
from amphora_contracts_research import (
    SyntheticEvidenceRecord,
    synthetic_evidence_schema,
    synthetic_evidence_schema_document,
)
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from .test_wire import ARTIFACT, SCHEMA, need


def record():
    return {"wire_version": "1", "authority": "synthetic", "need": need()["reference"], "criterion_id": "c1",
            "subject": ARTIFACT, "method": SCHEMA, "context": ARTIFACT, "category": "observation",
            "issuer": "fixture-publisher", "purpose": "fixture.measurement", "disposition": "supported"}


def test_public_payload_is_a_strict_synthetic_producer_claim_not_issuer_authentication():
    value = record()
    parsed = SyntheticEvidenceRecord.model_validate_json(json.dumps(value))
    assert json.loads(parsed.model_dump_json()) == value
    document = synthetic_evidence_schema_document()
    schema = json.loads(document)
    assert "$id" not in schema
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(value)
    assert synthetic_evidence_schema().sha256 == hashlib.sha256(document).hexdigest()
    for mode in ("validation", "serialization"):
        Draft202012Validator(SyntheticEvidenceRecord.model_json_schema(mode=mode)).validate(value)


@pytest.mark.parametrize("mutation", [
    lambda x: x.update(authority="scientific"),
    lambda x: x.update(category="logical_truth"),
    lambda x: x.update(disposition="certain"),
    lambda x: x.update(issuer=""),
    lambda x: x.update(authenticated=True),
    lambda x: x.update(confidence=1),
])
def test_shape_cannot_promote_synthetic_evidence_or_claim_authentication(mutation):
    value = record()
    mutation(value)
    with pytest.raises(ValidationError):
        SyntheticEvidenceRecord.model_validate_json(json.dumps(value))
    assert list(Draft202012Validator(SyntheticEvidenceRecord.model_json_schema()).iter_errors(value))
