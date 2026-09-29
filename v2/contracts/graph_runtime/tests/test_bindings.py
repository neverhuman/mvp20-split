"""New node tags require an explicitly versioned observation, preserving old readers."""

import json

import pytest
from amphora_contracts_graph_runtime import GraphNodeViewV2, GraphNodeViewV3
from pydantic import ValidationError


@pytest.mark.parametrize("kind", ["artifact_project", "artifact_materialize"])
def test_binding_tags_are_separate_from_legacy_observation(kind):
    raw = json.dumps({"activation_id": "a" * 64,
        "path": {"schema_version": "2", "node_id": "convert", "occurrences": []},
        "kind": kind, "status": "ready", "reason_code": None})
    assert GraphNodeViewV3.model_validate_json(raw).kind == kind
    with pytest.raises(ValidationError):
        GraphNodeViewV2.model_validate_json(raw)
