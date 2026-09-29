"""Bounded consistent graph observations; cursors confer no execution authority."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, Scope, WireModel
from pydantic import Field

from .bindings import GraphNodeViewV3
from .values import MissingValue, PresentValue

Revision = Annotated[int, Field(ge=0, le=9007199254740991)]
Cursor = Annotated[str, Field(min_length=1, max_length=4096)]


class GraphReadCut(WireModel):
    scope: Scope
    run_id: Identifier
    plan_sha256: Digest
    revision: Revision
    frontier_revision: Revision


class GraphReadQuery(WireModel):
    scope_key: Digest | None = None
    frontier_only: bool = False


class GraphReadBudget(WireModel):
    limit: Annotated[int, Field(ge=1, le=9007199254740991)]
    reserved: Revision
    spent: Revision


class GraphReadSnapshot(WireModel):
    cut: GraphReadCut
    status: Literal["running", "completed", "cancelled", "failed", "blocked"]
    budget: GraphReadBudget
    query: GraphReadQuery
    node_count: Annotated[int, Field(ge=0, le=100000)]
    snapshot_token: Cursor
    event_cursor: Cursor


class GraphSnapshotPage(WireModel):
    schema_version: Literal["1"] = "1"
    snapshot: GraphReadSnapshot
    nodes: Annotated[tuple[GraphNodeViewV3, ...], Field(max_length=100)]
    next_cursor: Cursor | None


class GraphOutputSummary(WireModel):
    port: Identifier
    kind: Literal["boolean", "integer", "number", "string", "artifact", "collection"]
    item_count: Annotated[int, Field(ge=0, le=10000)]
    missing_count: Annotated[int, Field(ge=0, le=10000)]
    artifact: ArtifactRef | None = None


class GraphAttemptView(WireModel):
    attempt_id: Identifier
    invocation_id: Identifier
    worker_id: Identifier
    fence: Annotated[int, Field(ge=1, le=9007199254740991)]
    status: Literal["leased", "succeeded", "abstained", "failed", "expired", "cancelled", "uncertain"]
    settled: bool
    completion_id: Identifier | None
    canonical_result: bool


class GraphNodeDetail(WireModel):
    schema_version: Literal["1"] = "1"
    cut: GraphReadCut
    node: GraphNodeViewV3
    scope_key: Digest
    parent_activation_id: Digest | None
    outputs: Annotated[tuple[GraphOutputSummary, ...], Field(max_length=64)]
    attempts: Annotated[tuple[GraphAttemptView, ...], Field(max_length=100)]
    next_cursor: Cursor | None


class GraphValueItem(WireModel):
    index: Annotated[int, Field(ge=0, le=9999)]
    value: PresentValue | MissingValue


class GraphValuePage(WireModel):
    schema_version: Literal["1"] = "1"
    cut: GraphReadCut
    activation_id: Digest
    port: Identifier
    item_count: Annotated[int, Field(ge=0, le=10000)]
    items: Annotated[tuple[GraphValueItem, ...], Field(max_length=100)]
    next_cursor: Cursor | None


class GraphInvalidation(WireModel):
    event_id: Identifier
    revision: Revision
    kind: Literal["run_changed"] = "run_changed"


class GraphInvalidationPage(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    run_id: Identifier
    observed_revision: Revision
    entries: Annotated[tuple[GraphInvalidation, ...], Field(max_length=100)]
    next_cursor: Cursor
    has_more: bool
