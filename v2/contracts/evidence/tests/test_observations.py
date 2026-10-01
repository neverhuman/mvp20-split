import json

import pytest
from amphora_contracts_evidence import ObserveSourceIdentity, SourceIdentityObservation, SourceIdentityStatus
from jsonschema import Draft202012Validator
from pydantic import ValidationError


def test_observation_shapes_preserve_explicit_pending_and_no_authority():
    request = {"wire_version": "1", "observation_id": "lookup-1",
               "trace": {"scope": {"tenant_id": "fixture", "project_id": "source"},
                         "trace_id": "trace", "sha256": "a" * 64}}
    result = {"wire_version": "1", "request": request, "kind": "unresolved", "resolution": None,
              "scientific_authority": "none"}
    values = [(ObserveSourceIdentity, request), (SourceIdentityObservation, result),
              (SourceIdentityStatus, {"wire_version": "1", "request": request, "result": None}),
              (SourceIdentityStatus, {"wire_version": "1", "request": request, "result": result})]
    for model, value in values:
        parsed = model.model_validate_json(json.dumps(value))
        for mode in ("validation", "serialization"):
            Draft202012Validator(model.model_json_schema(mode=mode)).validate(json.loads(parsed.model_dump_json()))
        with pytest.raises(ValidationError):
            model.model_validate_json(json.dumps(value | {"unexpected_authority": True}))
    with pytest.raises(ValidationError):
        SourceIdentityObservation.model_validate_json(json.dumps(result | {"scientific_authority": "accepted"}))
