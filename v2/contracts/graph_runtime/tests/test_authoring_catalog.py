"""Public form metadata is bounded and does not claim live tool or scientific eligibility."""

import base64
import json

import pytest
from amphora_contracts_graph_runtime import DefinitionSchema, DefinitionUniverse
from pydantic import ValidationError


def universe():
    return {"scope": {"tenant_id": "tenant", "project_id": "project"}, "universe_sha256": "a" * 64,
        "reviewed_tools": [], "schemas": []}


def test_universe_authority_and_schema_bounds_are_explicit():
    record = universe()
    assert DefinitionUniverse.model_validate_json(json.dumps(record)).authority == "compiler_configuration"
    with pytest.raises(ValidationError):
        DefinitionUniverse.model_validate_json(json.dumps({**record, "authority": "execution_approved"}))
    reference = {"schema_id": "shape", "version": "1", "sha256": "b" * 64}
    with pytest.raises(ValidationError):
        DefinitionUniverse.model_validate_json(json.dumps({**record, "schemas": [reference] * 257}))
    body = {key: record[key] for key in ("scope", "universe_sha256")}
    body.update(reference=reference, schema_bytes_base64=base64.b64encode(b"{}").decode())
    assert DefinitionSchema.model_validate_json(json.dumps(body)).reference.schema_id == "shape"
    for wrong in ("", "!" * 4, "aaaaa", "a" * 87385, base64.b64encode(b"a" * 65537).decode()):
        with pytest.raises(ValidationError):
            DefinitionSchema.model_validate_json(json.dumps({**body, "schema_bytes_base64": wrong}))
