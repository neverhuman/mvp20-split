import json

import pytest
from amphora_contracts_evidence import SourceRightsRevision
from jsonschema import Draft202012Validator, FormatChecker
from pydantic import ValidationError


def example():
    return {"wire_version": "1", "reference": {"scope": {"tenant_id": "fixture", "project_id": "rights"},
            "rights_id": "local-audit", "revision": 1}, "supersedes": None, "status": "granted",
            "allowed_uses": ["read", "process"], "expires_at": "2027-01-01T00:00:00Z", "retention": "retain_audit_payload"}


def test_rights_shapes_preserve_aware_expiry_and_explicit_retention():
    record = SourceRightsRevision.model_validate_json(json.dumps(example()))
    assert record.expires_at.utcoffset().total_seconds() == 0
    for mode in ("validation", "serialization"):
        schema = SourceRightsRevision.model_json_schema(mode=mode)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(json.loads(record.model_dump_json()))


@pytest.mark.parametrize("patch", [
    {"expires_at": "2027-01-01T00:00:00"}, {"expires_at": 1234567890},
    {"retention": "delete_later"}, {"allowed_uses": ["scientific_acceptance"]},
    {"allowed_uses": ["read", "read", "read"]}, {"wire_version": "2"}, {"accepted": True},
])
def test_unsupported_rights_wire_values_fail(patch):
    with pytest.raises(ValidationError):
        SourceRightsRevision.model_validate_json(json.dumps(example() | patch))
