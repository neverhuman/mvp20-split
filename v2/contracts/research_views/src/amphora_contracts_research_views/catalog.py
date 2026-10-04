"""Reviewed capabilities bind result schemas, never executable browser routes."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_core import SchemaRef, WireModel
from amphora_contracts_research import ExperimentRevisionRef
from pydantic import Field

from .projections import ObservationSeriesPage, PropertyViewPage, SpecimenViewPage


class ResearchViewCapability(WireModel):
    view_id: Literal["specimens", "properties", "observation_series"]
    version: Literal["1"]
    result_schema: SchemaRef


class ResearchViewLimits(WireModel):
    rows: Literal[16]
    selected_observations: Literal[128]
    series_points: Literal[256]
    response_bytes: Literal[1048576]
    source_fetch: Literal["separate_data_authority"]


class ResearchViewCatalog(WireModel):
    wire_version: Literal["1"]
    owner: Literal["research"]
    experiment: ExperimentRevisionRef
    views: Annotated[
        tuple[ResearchViewCapability, ...], Field(min_length=3, max_length=3)
    ]
    limits: ResearchViewLimits


def research_view_schema(view_id):
    name, model = {
        "specimens": ("specimen-view-page", SpecimenViewPage),
        "properties": ("property-view-page", PropertyViewPage),
        "observation_series": ("observation-series-page", ObservationSeriesPage),
    }[view_id]
    schema = model.model_json_schema(mode="serialization")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"urn:amphora:research-views.{name}:1:serialization"
    raw = (
        json.dumps(
            schema,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    return SchemaRef(
        schema_id=f"research-views.{name}",
        version="1",
        sha256=hashlib.sha256(raw).hexdigest(),
    )
