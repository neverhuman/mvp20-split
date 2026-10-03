"""Operational progress is distinct from a completed policy interpretation's scientific uncertainty."""
from typing import Annotated, Literal

from amphora_contracts_core import Identifier, Scope, WireModel
from pydantic import Field

from .interpretation import (
    AssessObservationUseRequest,
    NormalizationProjection,
    NormalizeObservationRequest,
    ObservationUseProjection,
)

InterpretationRequest = Annotated[NormalizeObservationRequest | AssessObservationUseRequest,Field(discriminator="kind")]
InterpretationProjection = Annotated[NormalizationProjection | ObservationUseProjection,Field(discriminator="kind")]


class InterpretationSelection(WireModel):
    scope: Scope
    kind: Literal["normalization","observation-use"]
    interpretation_id: Identifier


class InterpretationPending(WireModel):
    status: Literal["pending"]


class InterpretationComplete(WireModel):
    status: Literal["interpreted"]
    projection: InterpretationProjection


class InterpretationStatus(WireModel):
    wire_version: Literal["1"]
    request: InterpretationRequest
    actor_id: Identifier
    outcome: Annotated[InterpretationPending | InterpretationComplete,Field(discriminator="status")]
