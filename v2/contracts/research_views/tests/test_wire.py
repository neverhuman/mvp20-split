"""Bounded shape/schema parity; static synthetic fixtures confer no authority."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_research_views import (
    ObservationSeriesPage,
    ObservationSeriesRequest,
    PropertyViewPage,
    PropertyViewRequest,
    ResearchViewCatalog,
    SpecimenViewPage,
    SpecimenViewRequest,
    research_view_schema,
)
from jsonschema import Draft202012Validator
from pydantic import ValidationError

CASES = json.loads((Path(__file__).parent / "fixtures/views.json").read_text())
MODELS = {
    "specimen_request": SpecimenViewRequest,
    "property_request": PropertyViewRequest,
    "series_request": ObservationSeriesRequest,
    "specimen_page": SpecimenViewPage,
    "property_page": PropertyViewPage,
    "series_page": ObservationSeriesPage,
    "catalog": ResearchViewCatalog,
}


@pytest.mark.parametrize("name", MODELS)
def test_shape_and_schema_parity(name):
    record = MODELS[name].model_validate_json(json.dumps(CASES[name]))
    assert record.model_dump(mode="json") == CASES[name]
    for mode in ("validation", "serialization"):
        Draft202012Validator(MODELS[name].model_json_schema(mode=mode)).validate(
            CASES[name]
        )
    with pytest.raises(ValidationError):
        MODELS[name].model_validate_json(
            json.dumps({**CASES[name], "authority_override": "accepted"})
        )


@pytest.mark.parametrize(
    "name,field,value",
    [
        ("specimen_request", "limit", 17),
        ("specimen_request", "limit", True),
        ("property_request", "limit", 0),
        ("series_request", "limit", 257),
        ("series_request", "limit", 1.0),
        ("property_request", "observations", []),
        ("property_page", "authority", "scientifically_accepted"),
        ("property_page", "selection_scope", "all_project_results"),
        ("catalog", "owner", "runtime"),
        ("series_request", "position", {"query_sha256": "0" * 64, "offset": 4097}),
    ],
)
def test_invalid_bounds_and_authority_fail(name, field, value):
    raw = copy.deepcopy(CASES[name])
    raw[field] = value
    with pytest.raises(ValidationError):
        MODELS[name].model_validate_json(json.dumps(raw))


@pytest.mark.parametrize(
    "name,field,maximum",
    [
        ("specimen_page", "rows", 16),
        ("property_page", "rows", 16),
        ("series_page", "points", 256),
        ("property_request", "observations", 128),
    ],
)
def test_array_bounds(name, field, maximum):
    raw = copy.deepcopy(CASES[name])
    raw[field] = raw[field][:1] * (maximum + 1)
    with pytest.raises(ValidationError):
        MODELS[name].model_validate_json(json.dumps(raw))


@pytest.mark.parametrize("name", ["specimens", "properties", "observation_series"])
def test_catalog_schema_is_exact_published_serialization(name):
    reference = research_view_schema(name)
    schema = (
        Path(__file__).absolute().parents[2]
        / "schemas/v1"
        / (reference.schema_id + ".serialization.json")
    )
    assert hashlib.sha256(schema.read_bytes()).hexdigest() == reference.sha256
