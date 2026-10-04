"""Bounded exact-revision read DTOs; Knowledge owns membership and continuation policy."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, SchemaRef, WireModel
from pydantic import Field

from .records import DomainAssertion, DomainEntity
from .references import AssertionRevisionRef, DomainRevisionRef, EntityRevisionRef

HistoryMode = Literal["current", "retained"]


class GraphViewPosition(WireModel):
    query_sha256: Digest
    entity_offset: Annotated[int, Field(ge=0, le=4096)]
    assertion_offset: Annotated[int, Field(ge=0, le=8192)]


class GraphEntitySearchRequest(WireModel):
    wire_version: Literal["1"]
    revision: DomainRevisionRef
    text: Annotated[str, Field(max_length=128)] = ""
    entity_type: Identifier | None = None
    history: HistoryMode = "current"
    limit: Annotated[int, Field(ge=1, le=50)] = 50
    position: GraphViewPosition | None = None


class GraphNeighborhoodRequest(WireModel):
    wire_version: Literal["1"]
    revision: DomainRevisionRef
    focus: EntityRevisionRef
    radius: Annotated[int, Field(ge=0, le=2)] = 1
    history: HistoryMode = "current"
    entity_limit: Annotated[int, Field(ge=1, le=64)] = 64
    assertion_limit: Annotated[int, Field(ge=1, le=128)] = 128
    position: GraphViewPosition | None = None


class GraphEntitySummary(WireModel):
    reference: EntityRevisionRef
    entity_type: Identifier
    label: Annotated[str, Field(min_length=1, max_length=512)]
    is_latest: bool
    alias_target: EntityRevisionRef | None


class GraphAssertionSummary(WireModel):
    reference: AssertionRevisionRef
    subject: EntityRevisionRef
    predicate: Identifier
    object: EntityRevisionRef
    polarity: Literal["affirmed", "negated"]
    posture: Literal["reported", "hypothesis", "unresolved"]
    is_latest: bool
    retracted: bool


class GraphEntitySearchPage(WireModel):
    wire_version: Literal["1"]
    request: GraphEntitySearchRequest
    query_sha256: Digest
    total: Annotated[int, Field(ge=0, le=4096)]
    entities: Annotated[tuple[GraphEntitySummary, ...], Field(max_length=50)]
    next_position: GraphViewPosition | None


class GraphNeighborhoodPage(WireModel):
    wire_version: Literal["1"]
    request: GraphNeighborhoodRequest
    query_sha256: Digest
    entity_total: Annotated[int, Field(ge=0, le=4096)]
    assertion_total: Annotated[int, Field(ge=0, le=8192)]
    entities: Annotated[tuple[GraphEntitySummary, ...], Field(max_length=64)]
    assertions: Annotated[tuple[GraphAssertionSummary, ...], Field(max_length=128)]
    unresolved_entities: Annotated[tuple[EntityRevisionRef, ...], Field(max_length=320)]
    next_position: GraphViewPosition | None


class GraphEntitySelection(WireModel):
    kind: Literal["entity"]
    reference: EntityRevisionRef


class GraphAssertionSelection(WireModel):
    kind: Literal["assertion"]
    reference: AssertionRevisionRef


class GraphObjectRequest(WireModel):
    wire_version: Literal["1"]
    revision: DomainRevisionRef
    selection: Annotated[
        GraphEntitySelection | GraphAssertionSelection, Field(discriminator="kind")
    ]


class GraphEntityDetail(WireModel):
    kind: Literal["entity"]
    record: DomainEntity
    is_latest: bool
    alias_target: EntityRevisionRef | None


class GraphAssertionDetail(WireModel):
    kind: Literal["assertion"]
    record: DomainAssertion
    is_latest: bool
    retracted: bool


class GraphObjectDetail(WireModel):
    wire_version: Literal["1"]
    request: GraphObjectRequest
    detail: Annotated[
        GraphEntityDetail | GraphAssertionDetail, Field(discriminator="kind")
    ]


class GraphExploreCapability(WireModel):
    view_id: Literal["entity_search", "neighborhood", "object_detail"]
    version: Literal["1"]
    result_schema: SchemaRef


class GraphExploreLimits(WireModel):
    search_page: Literal[50]
    entity_page: Literal[64]
    assertion_page: Literal[128]
    radius: Literal[2]
    response_bytes: Literal[1048576]
    source_fetch: Literal["separate_data_authority"]


class GraphExploreCatalog(WireModel):
    wire_version: Literal["1"]
    owner: Literal["knowledge"]
    revision: DomainRevisionRef
    views: Annotated[
        tuple[GraphExploreCapability, ...], Field(min_length=3, max_length=3)
    ]
    limits: GraphExploreLimits


def graph_explore_schema(view_id: str) -> SchemaRef:
    """Pin the published v1 serialization schema, including its declared URN."""
    views = {
        "entity_search": ("entity-search-page", GraphEntitySearchPage),
        "neighborhood": ("neighborhood-page", GraphNeighborhoodPage),
        "object_detail": ("object-detail", GraphObjectDetail),
    }
    if view_id not in views:
        raise ValueError("unknown_explore_view")
    name, model = views[view_id]
    schema_id = "knowledge." + name
    document = model.model_json_schema(mode="serialization")
    document["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    document["$id"] = f"urn:amphora:{schema_id}:1:serialization"
    raw = (
        json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    return SchemaRef(
        schema_id=schema_id, version="1", sha256=hashlib.sha256(raw).hexdigest()
    )
