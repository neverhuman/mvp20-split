import json

import pytest
from amphora_contracts_artifacts import PublicationObservation
from jsonschema import Draft202012Validator
from pydantic import ValidationError


@pytest.mark.parametrize("outcome", [
    {"status": "pending"},
    {"status": "rejected", "reason_code": "upload_not_ready"},
    {"status": "uploaded", "receipt": {"upload_id": "upload-1",
        "scope": {"tenant_id": "example", "project_id": "demo"},
        "content": {"sha256": "a" * 64, "size_bytes": 4, "media_type": "text/plain",
                    "schema_ref": {"schema_id": "example.text", "version": "1", "sha256": "b" * 64}}}},
])
def test_original_command_observation_is_portable(outcome):
    raw = {"identity": {"command_family": "artifacts.begin_upload", "command_id": "command-1",
        "actor_id": "worker", "scope": {"tenant_id": "example", "project_id": "demo"}},
        "operation_id": "operation-1", "request_sha256": "c" * 64, "outcome": outcome}
    observation = PublicationObservation.model_validate_json(json.dumps(raw))
    Draft202012Validator(PublicationObservation.model_json_schema()).validate(observation.model_dump())
    for invalid in ({"outcome": {"status": "complete"}}, {"request_sha256": "wrong"},
                    {"outcome": {"status": "pending", "receipt": {}}}):
        with pytest.raises(ValidationError):
            PublicationObservation.model_validate_json(json.dumps({**raw, **invalid}))
