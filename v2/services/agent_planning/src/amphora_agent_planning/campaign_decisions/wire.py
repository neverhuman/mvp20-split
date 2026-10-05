"""Private reviewed configuration DTOs; factories and policies own authority checks."""

from typing import Annotated, Literal

from amphora_contracts_campaigns import ContextPin, ScalarConstant
from amphora_contracts_core import (
    ArtifactRef,
    Digest,
    Identifier,
    SafePositiveInt,
    WireModel,
)
from amphora_contracts_graph_runtime import GraphReadCut
from amphora_contracts_planning import CampaignNodeAddress, EngagementRef
from pydantic import Field, TypeAdapter

Action = Literal['abstain', 'request_evidence', 'propose_campaign']
SideEffect = Literal['pure', 'idempotent', 'external']
FiniteNumber = Annotated[float, Field(ge=-1e100, le=1e100, allow_inf_nan=False)]


class FutureBoundaryRecord(WireModel):
    campaign_id: Identifier
    revision: SafePositiveInt
    context: Annotated[tuple[ContextPin, ...], Field(min_length=2, max_length=256)]
    max_nodes: Annotated[int, Field(ge=1, le=4096)]
    max_scopes: Annotated[int, Field(ge=1, le=1024)]
    max_depth: Annotated[int, Field(ge=0, le=16)]
    max_iterations: Annotated[int, Field(ge=1, le=10000)]
    max_tool_timeout: Annotated[int, Field(ge=1, le=86400)]
    side_effects: Annotated[tuple[SideEffect, ...], Field(min_length=1, max_length=3)]


class EnumerationRecord(WireModel):
    kind: Literal['enumeration']
    values: Annotated[tuple[ScalarConstant, ...], Field(min_length=1, max_length=64)]


class NumericRangeRecord(WireModel):
    kind: Literal['numeric_range']
    scalar: Literal['integer', 'number']
    unit: Annotated[str, Field(min_length=1, max_length=64)]
    minimum: FiniteNumber
    maximum: FiniteNumber


class AdjustmentPermitRecord(WireModel):
    target: CampaignNodeAddress
    input_name: Identifier
    previous_value_sha256: Digest
    bounds: Annotated[EnumerationRecord | NumericRangeRecord, Field(discriminator='kind')]


class DecisionDeclarationRecord(WireModel):
    format: Literal['planning-campaign-decision.v1']
    declaration_artifact_id: Identifier
    engagement: EngagementRef
    objective: ArtifactRef
    policy: ArtifactRef
    runtime_cut: GraphReadCut | None
    allowed_actions: Annotated[tuple[Action, ...], Field(min_length=1, max_length=3)]
    eligibility_context: Identifier
    future: FutureBoundaryRecord | None
    adjustments: Annotated[tuple[AdjustmentPermitRecord, ...], Field(max_length=64)]


class PublishedDecisionDeclarationRecord(WireModel):
    format: Literal['planning-campaign-decision.v2']
    engagement: EngagementRef
    objective: ArtifactRef
    policy: ArtifactRef
    runtime_cut: GraphReadCut | None
    allowed_actions: Annotated[tuple[Action, ...], Field(min_length=1, max_length=3)]
    eligibility_context: Identifier
    future: FutureBoundaryRecord | None
    adjustments: Annotated[tuple[AdjustmentPermitRecord, ...], Field(max_length=64)]


DECLARATION = TypeAdapter(Annotated[
    DecisionDeclarationRecord | PublishedDecisionDeclarationRecord, Field(discriminator='format')])
