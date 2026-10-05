"""Bounded immutable DTOs; cross-record policy and hashing remain Runtime-owned."""

from typing import Annotated, Literal

from amphora_contracts_core import (
    ArtifactRef,
    Digest,
    Identifier,
    SafePositiveInt,
    Scope,
    WireModel,
)
from amphora_contracts_graph_runtime import GraphNodeViewV3, GraphReadCut
from amphora_contracts_planning import EngagementRequest
from pydantic import Field


class SupervisionRef(WireModel):
    scope: Scope
    run_id: Identifier
    decision_id: Identifier


class SupervisionNodeRead(WireModel):
    node: GraphNodeViewV3
    state_sha256: Digest
    outputs_sha256: Digest


class SupervisionSnapshot(WireModel):
    schema_version: Literal['1'] = '1'
    cut: GraphReadCut
    targets: Annotated[tuple[Digest, ...], Field(min_length=1, max_length=64)]
    reads: Annotated[tuple[SupervisionNodeRead, ...], Field(min_length=1, max_length=256)]
    footprint_sha256: Digest
    relevant_sha256: Digest


class SupervisionLineage(WireModel):
    ordinal: Annotated[int, Field(ge=1, le=16)]
    root_request_sha256: Digest | None
    parent_request_sha256: Digest | None


class SupervisionRequest(WireModel):
    schema_version: Literal['1'] = '1'
    reference: SupervisionRef
    checkpoint_id: Identifier
    policy: ArtifactRef
    snapshot: SupervisionSnapshot
    planning_request: EngagementRequest
    planning_request_sha256: Digest
    deadline_unix_ms: SafePositiveInt
    lineage: SupervisionLineage
