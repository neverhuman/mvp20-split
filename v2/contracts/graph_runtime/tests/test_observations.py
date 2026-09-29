"""Read DTO bounds and additive wire round trips; tokens remain owner policy."""

import json

import pytest
from amphora_contracts_graph_runtime import (
    GraphInvalidationPage,
    GraphNodeDetail,
    GraphReadQuery,
    GraphSnapshotPage,
    GraphValuePage,
)
from jsonschema import Draft202012Validator
from pydantic import ValidationError

SCOPE = {"tenant_id": "test", "project_id": "observation"}
CUT = {"scope": SCOPE, "run_id": "run", "plan_sha256": "a" * 64, "revision": 0, "frontier_revision": 0}
NODE = {"activation_id": "b" * 64, "path": {"schema_version": "2", "node_id": "finish", "occurrences": []},
        "kind": "finish", "status": "ready", "reason_code": None}


@pytest.mark.parametrize("model,payload", [
    (GraphSnapshotPage, {"snapshot": {"cut": CUT, "status": "running", "budget": {"limit": 2, "reserved": 0, "spent": 0},
        "query": {}, "node_count": 1, "snapshot_token": "signed", "event_cursor": "signed-events"}, "nodes": [NODE], "next_cursor": None}),
    (GraphNodeDetail, {"cut": CUT, "node": NODE, "scope_key": "c" * 64, "parent_activation_id": None, "outputs": [], "attempts": [], "next_cursor": None}),
    (GraphValuePage, {"cut": CUT, "activation_id": "b" * 64, "port": "values", "item_count": 2, "items": [
        {"index": 0, "value": {"kind": "integer", "value": 17}},
        {"index": 1, "value": {"kind": "missing", "member_id": "m1", "reason_code": "failed"}}], "next_cursor": None}),
    (GraphInvalidationPage, {"scope": SCOPE, "run_id": "run", "observed_revision": 1,
        "entries": [{"event_id": "e1", "revision": 1}], "next_cursor": "signed", "has_more": False}),
])
def test_observation_root_roundtrip_and_schema(model, payload):
    value = model.model_validate_json(json.dumps(payload))
    serialized = value.model_dump_json()
    assert model.model_validate_json(serialized) == value
    Draft202012Validator(model.model_json_schema()).validate(json.loads(serialized))


@pytest.mark.parametrize("query", [{"frontier_only": "true"}, {"scope_key": "unknown"}, {"sql": "arbitrary"}])
def test_query_is_finite_and_strict(query):
    with pytest.raises(ValidationError):
        GraphReadQuery.model_validate_json(json.dumps(query))


def test_invalidation_page_is_bounded_and_not_an_execution_patch():
    raw = {"scope": SCOPE, "run_id": "run", "observed_revision": 101,
        "entries": [{"event_id": f"event-{index}", "revision": index} for index in range(101)], "next_cursor": "signed", "has_more": False}
    with pytest.raises(ValidationError):
        GraphInvalidationPage.model_validate_json(json.dumps(raw))
    raw["entries"] = [{"event_id": "e", "revision": 1, "kind": "execute"}]
    with pytest.raises(ValidationError):
        GraphInvalidationPage.model_validate_json(json.dumps(raw))
