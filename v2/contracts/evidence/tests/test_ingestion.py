import json

import pytest
from amphora_contracts_evidence import PreparedSource, RetainPreparedSource
from jsonschema import Draft202012Validator
from pydantic import ValidationError


@pytest.fixture
def source():
    scope = {"tenant_id": "synthetic", "project_id": "fixture"}
    artifact = {"scope": scope, "artifact_id": "raw", "sha256": "a" * 64, "size_bytes": 0,
                "media_type": "application/octet-stream",
                "schema_ref": {"schema_id": "fixture", "version": "1", "sha256": "b" * 64}}
    return {"wire_version": "1", "reference": {"scope": scope, "source_id": "source",
            "revision_id": "r1", "raw": artifact}, "delivery": {"issuer_id": "fixture", "delivery_id": "d1"},
            "method": {"connector_id": "fixture", "connector_version": "1", "configuration_sha256": "c" * 64,
                       "format": "utf8_document"},
            "rights": {"scope": scope, "rights_id": "fixture", "revision": 1},
            "supersedes": None, "completeness": "complete"}


@pytest.mark.parametrize("model", [PreparedSource, RetainPreparedSource])
def test_ingestion_contracts_roundtrip_without_acceptance_authority(source, model):
    ref = source["reference"]
    value = ({"wire_version": "1", "source": ref, "content_json_utf8": "{}", "sha256": "d" * 64,
              "schema_ref": ref["raw"]["schema_ref"], "disposition": "unresolved", "warnings": []}
             if model is PreparedSource else
             {"wire_version": "1", "source": source, "trace_id": "trace", "output": ref["raw"]})
    parsed = model.model_validate_json(json.dumps(value))
    for mode in ("validation", "serialization"):
        Draft202012Validator(model.model_json_schema(mode=mode)).validate(json.loads(parsed.model_dump_json()))
    for patch in ({"wire_version": "2"}, {"scientifically_accepted": True}, {"source": None}):
        with pytest.raises(ValidationError):
            model.model_validate_json(json.dumps(value | patch))
