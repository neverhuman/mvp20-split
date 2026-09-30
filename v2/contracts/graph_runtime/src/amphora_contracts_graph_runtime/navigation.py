"""Scoped occurrence and authored-control projections; no client-inferred topology."""

from typing import Annotated, Literal

from amphora_contracts_campaigns import Occurrence
from amphora_contracts_core import Digest, Identifier, WireModel
from pydantic import Field

from .bindings import GraphNodeViewV3
from .observations import Cursor, GraphReadCut


class GraphScopeView(WireModel):
    scope_key: Digest
    definition_path: Annotated[tuple[Identifier, ...], Field(max_length=16)]
    occurrences: Annotated[tuple[Occurrence, ...], Field(max_length=16)]
    parent_activation_id: Digest | None
    status: Literal["active", "completed", "failed", "skipped", "blocked"]
    node_count: Annotated[int, Field(ge=0, le=256)]


class GraphScopePage(WireModel):
    schema_version: Literal["1"] = "1"
    cut: GraphReadCut
    parent_activation_id: Digest | None
    scope_count: Annotated[int, Field(ge=0, le=100000)]
    scopes: Annotated[tuple[GraphScopeView, ...], Field(max_length=100)]
    next_cursor: Cursor | None


class GraphTopologyQuery(WireModel):
    focus_activation_id: Digest | None = None
    radius: Annotated[int, Field(ge=0, le=2)] = 1


class GraphTopologyNode(WireModel):
    activation: GraphNodeViewV3
    child_scope_count: Annotated[int, Field(ge=0, le=100000)]


class GraphControlLink(WireModel):
    source: Digest
    target: Digest
    route: Literal["next", "true", "false"]


class GraphTopologyPage(WireModel):
    schema_version: Literal["1"] = "1"
    cut: GraphReadCut
    graph_scope: GraphScopeView
    query: GraphTopologyQuery
    node_count: Annotated[int, Field(ge=0, le=256)]
    edge_count: Annotated[int, Field(ge=0, le=1024)]
    nodes: Annotated[tuple[GraphTopologyNode, ...], Field(max_length=100)]
    edges: Annotated[tuple[GraphControlLink, ...], Field(max_length=1024)]
    next_cursor: Cursor | None
