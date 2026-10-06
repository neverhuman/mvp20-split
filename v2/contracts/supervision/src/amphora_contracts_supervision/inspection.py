"""Bounded owner-retained metadata; no raw prompt/capture or mutation authority."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, WireModel
from amphora_contracts_graph_runtime import GraphReadCut
from amphora_contracts_planning import (
    CallLimits,
    ContextEntry,
    ContextOmission,
    EngagementRef,
    ModelBinding,
)
from pydantic import Field

from .execution import CheckpointStopReason
from .requests import SupervisionLineage, SupervisionRef

Count = Annotated[int, Field(ge=0, le=9007199254740991)]
Token = Annotated[str, Field(min_length=1, max_length=4096)]
ObservationStatus = Literal['proposed', 'abstained', 'invalid', 'unavailable', 'policy_rejected', 'unknown']


class SupervisionInspectionCut(WireModel):
    cut: GraphReadCut
    epoch: Digest
    snapshot_token: Token


class CheckpointInspectionItem(WireModel):
    reference: SupervisionRef
    checkpoint_id: Identifier
    targets: Annotated[tuple[Digest, ...], Field(min_length=1, max_length=64)]
    eligibility_reason: Identifier | None
    requests: Count
    winner_kind: Literal['model_accepted', 'fallback', 'cancelled'] | None
    winner_reason: Identifier | None


class CheckpointInspectionPage(WireModel):
    schema_version: Literal['1'] = '1'
    snapshot: SupervisionInspectionCut
    total: Count
    items: Annotated[tuple[CheckpointInspectionItem, ...], Field(max_length=10)]
    next_cursor: Token | None


class CheckpointInspectionAttempt(WireModel):
    ordinal: Annotated[int, Field(ge=1, le=16)]
    status: ObservationStatus
    observation_sha256: Digest


class CheckpointRequestItem(WireModel):
    request_sha256: Digest
    lineage: SupervisionLineage
    engagement: EngagementRef
    planning_request_sha256: Digest
    model: ModelBinding
    prompt: ArtifactRef
    limits: CallLimits
    context_entries: Annotated[int, Field(ge=0, le=128)]
    context_omissions: Annotated[int, Field(ge=0, le=128)]
    report_stop_reason: CheckpointStopReason | None
    attempts: Annotated[tuple[CheckpointInspectionAttempt, ...], Field(max_length=16)]
    responses: Count
    disposition: Literal['repair', 'fallback'] | None
    disposition_reason: Identifier | None


class CheckpointRequestPage(WireModel):
    schema_version: Literal['1'] = '1'
    snapshot: SupervisionInspectionCut
    reference: SupervisionRef
    total: Count
    items: Annotated[tuple[CheckpointRequestItem, ...], Field(max_length=10)]
    next_cursor: Token | None


class IncludedCheckpointContext(WireModel):
    kind: Literal['included']
    entry: ContextEntry


class OmittedCheckpointContext(WireModel):
    kind: Literal['omitted']
    omission: ContextOmission


class CheckpointContextPage(WireModel):
    schema_version: Literal['1'] = '1'
    snapshot: SupervisionInspectionCut
    reference: SupervisionRef
    request_sha256: Digest
    total: Count
    items: Annotated[tuple[Annotated[IncludedCheckpointContext | OmittedCheckpointContext,
        Field(discriminator='kind')], ...], Field(max_length=10)]
    next_cursor: Token | None


class CheckpointResponseItem(WireModel):
    response_id: Identifier
    response_sha256: Digest
    attempt_ordinal: Annotated[int, Field(ge=1, le=16)]
    status: ObservationStatus
    reason_code: Identifier | None
    output_sha256: Digest
    captured_bytes: Annotated[int, Field(ge=0, le=65536)]
    output_complete: bool
    capture: ArtifactRef | None
    selected_by_winner: bool


class CheckpointResponsePage(WireModel):
    schema_version: Literal['1'] = '1'
    snapshot: SupervisionInspectionCut
    reference: SupervisionRef
    request_sha256: Digest
    total: Count
    items: Annotated[tuple[CheckpointResponseItem, ...], Field(max_length=10)]
    next_cursor: Token | None
