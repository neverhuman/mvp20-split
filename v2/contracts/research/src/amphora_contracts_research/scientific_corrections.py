"""Exact historical correction views and explicit future-campaign dependency queries."""
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, SafePositiveInt, WireModel
from pydantic import Field

from .identity import MaterialStateRevisionRef
from .interpretation import InterpretationRef
from .materials import MaterialStateRevision
from .observations import ObservationRevision, ObservationRevisionRef
from .scientific_decisions import ScientificDecisionRef


class ObservationCorrectionView(WireModel):
    wire_version: Literal["1"]
    policy: Literal["future_campaigns_only"]
    before: ObservationRevision
    after: ObservationRevision
    changed_fields: Annotated[tuple[Literal["source","binding","value","quality"], ...],Field(max_length=4)]


class MaterialStateCorrectionView(WireModel):
    wire_version: Literal["1"]
    policy: Literal["future_campaigns_only"]
    before: MaterialStateRevision
    after: MaterialStateRevision
    changed_fields: Annotated[tuple[Literal["candidate","preparation","features"], ...],Field(max_length=3)]


class MaterialStateImpactRequest(WireModel):
    wire_version: Literal["1"]
    source: MaterialStateRevisionRef
    after: ScientificDecisionRef | None
    limit: Annotated[SafePositiveInt,Field(le=128)]


class InterpretationImpactRequest(WireModel):
    wire_version: Literal["1"]
    source: ArtifactRef | ObservationRevisionRef | MaterialStateRevisionRef
    after: InterpretationRef | None
    limit: Annotated[SafePositiveInt,Field(le=128)]


class InterpretationImpactPage(WireModel):
    wire_version: Literal["1"]
    policy: Literal["future_campaigns_only"]
    interpretations: Annotated[tuple[InterpretationRef, ...],Field(max_length=128)]
    next_after: InterpretationRef | None
