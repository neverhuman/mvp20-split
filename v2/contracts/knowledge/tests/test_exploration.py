"""Public read shape and schema parity; placeholders confer no owner authority."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_knowledge import (
    GraphEntitySearchPage,
    GraphEntitySearchRequest,
    GraphExploreCatalog,
    GraphNeighborhoodPage,
    GraphNeighborhoodRequest,
    GraphObjectDetail,
    GraphObjectRequest,
    graph_explore_schema,
)
from jsonschema import Draft202012Validator
from pydantic import ValidationError

CASES = json.loads(
    (Path(__file__).parent / "fixtures/exploration.json").read_text(encoding="utf-8")
)
MODELS = {
    "search_request": GraphEntitySearchRequest,
    "search_page": GraphEntitySearchPage,
    "neighborhood_request": GraphNeighborhoodRequest,
    "neighborhood_page": GraphNeighborhoodPage,
    "object_request": GraphObjectRequest,
    "object_detail": GraphObjectDetail,
    "catalog": GraphExploreCatalog,
}


@pytest.mark.parametrize("name", MODELS)
def test_exploration_wire_and_published_schema_shapes(name):
    model, raw = MODELS[name], CASES[name]
    parsed = model.model_validate_json(json.dumps(raw))
    assert parsed.model_dump(mode="json") == raw
    for mode in ("validation", "serialization"):
        Draft202012Validator(model.model_json_schema(mode=mode)).validate(raw)


@pytest.mark.parametrize(
    "name,path,value",
    [
        ("search_request", ("limit",), 51),
        ("search_request", ("limit",), True),
        ("search_request", ("limit",), 1.0),
        ("search_request", ("text",), "x" * 129),
        ("search_request", ("history",), "scientifically_accepted"),
        ("neighborhood_request", ("radius",), 3),
        ("neighborhood_request", ("radius",), -1),
        ("neighborhood_request", ("entity_limit",), 65),
        ("neighborhood_request", ("assertion_limit",), 129),
        ("neighborhood_request", ("focus", "revision"), 0),
        ("catalog", ("owner",), "campaign-runtime"),
        ("catalog", ("limits", "response_bytes"), 2097152),
        ("catalog", ("limits", "source_fetch"), "authorized_by_graph"),
        ("object_request", ("selection", "kind"), "arbitrary_query"),
    ],
)
def test_unreviewed_policies_and_unbounded_queries_are_rejected(name, path, value):
    raw = copy.deepcopy(CASES[name])
    selected = raw
    for key in path[:-1]:
        selected = selected[key]
    selected[path[-1]] = value
    with pytest.raises(ValidationError):
        MODELS[name].model_validate_json(json.dumps(raw))


@pytest.mark.parametrize(
    "lane,bound", [("entities", 64), ("assertions", 128), ("unresolved_entities", 320)]
)
def test_neighborhood_response_cardinality_is_bounded(lane, bound):
    raw = copy.deepcopy(CASES["neighborhood_page"])
    raw[lane] = raw[lane] * (bound + 1)
    with pytest.raises(ValidationError):
        GraphNeighborhoodPage.model_validate_json(json.dumps(raw))


def test_continuation_and_detail_are_explicit_shapes_not_claimed_authority():
    raw = copy.deepcopy(CASES["search_request"])
    raw["position"] = {
        "query_sha256": "c" * 64,
        "entity_offset": 1,
        "assertion_offset": 0,
    }
    assert (
        GraphEntitySearchRequest.model_validate_json(
            json.dumps(raw)
        ).position.entity_offset
        == 1
    )
    raw["position"]["entity_offset"] = 4097
    with pytest.raises(ValidationError):
        GraphEntitySearchRequest.model_validate_json(json.dumps(raw))
    detail = copy.deepcopy(CASES["object_detail"])
    golden = json.loads(
        (Path(__file__).parent / "fixtures/golden.json").read_text(encoding="utf-8")
    )
    assertion = golden["snapshot"]["content"]["assertions"][0]
    detail["request"]["selection"] = {
        "kind": "assertion",
        "reference": assertion["reference"],
    }
    detail["detail"] = {
        "kind": "assertion",
        "record": assertion,
        "is_latest": False,
        "retracted": True,
    }
    assert GraphObjectDetail.model_validate_json(json.dumps(detail)).detail.retracted
    # Matching query digest, exact snapshot membership and history status are owner checks.


@pytest.mark.parametrize("name", ["entity_search", "neighborhood", "object_detail"])
def test_capability_schema_digest_matches_published_serialization(name):
    ref = graph_explore_schema(name)
    schema = (
        Path(__file__).absolute().parents[2]
        / "schemas/v1"
        / (ref.schema_id + ".serialization.json")
    )
    assert hashlib.sha256(schema.read_bytes()).hexdigest() == ref.sha256
    with pytest.raises(ValueError, match="unknown_explore_view"):
        graph_explore_schema("caller-selected-query")
