"""Public occurrence/navigation bounds and immutable serialization compatibility."""

import json

import pytest
from amphora_contracts_graph_runtime import (
    GraphScopePage,
    GraphTopologyPage,
    GraphTopologyQuery,
)
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from .test_observations import CUT, NODE

SCOPE = {"scope_key": "c" * 64, "definition_path": [], "occurrences": [], "parent_activation_id": None,
         "status": "active", "node_count": 1}


@pytest.mark.parametrize("model,payload", [
    (GraphScopePage, {"cut": CUT, "parent_activation_id": None, "scope_count": 1, "scopes": [SCOPE], "next_cursor": None}),
    (GraphTopologyPage, {"cut": CUT, "graph_scope": SCOPE, "query": {}, "node_count": 1, "edge_count": 0,
                         "nodes": [{"activation": NODE, "child_scope_count": 0}], "edges": [], "next_cursor": None}),
])
def test_navigation_public_root_roundtrip_and_schema(model, payload):
    value = model.model_validate_json(json.dumps(payload))
    assert model.model_validate_json(value.model_dump_json()) == value
    Draft202012Validator(model.model_json_schema()).validate(json.loads(value.model_dump_json()))


@pytest.mark.parametrize("query", [{"radius": -1}, {"radius": 3}, {"radius": True}, {"radius": "1"},
                                   {"focus_activation_id": "unknown"}, {"cypher": "MATCH (n) RETURN n"}])
def test_neighborhood_query_has_only_bounded_typed_filters(query):
    with pytest.raises(ValidationError):
        GraphTopologyQuery.model_validate_json(json.dumps(query))


def test_scope_page_cannot_expand_all_occurrences_in_one_response():
    with pytest.raises(ValidationError):
        GraphScopePage.model_validate_json(json.dumps({"cut": CUT, "parent_activation_id": None,
            "scope_count": 101, "scopes": [SCOPE] * 101, "next_cursor": None}))
