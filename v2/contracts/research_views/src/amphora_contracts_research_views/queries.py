"""Exact selected evidence, never an implicit latest-state or project-wide query."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, WireModel
from amphora_contracts_research import ExperimentRevisionRef, ObservationRevisionRef
from pydantic import Field


class ResearchViewPosition(WireModel):
    query_sha256: Digest
    offset: Annotated[int, Field(ge=0, le=4096)]


class SpecimenViewRequest(WireModel):
    wire_version: Literal["1"]
    experiment: ExperimentRevisionRef
    limit: Annotated[int, Field(ge=1, le=16)] = 16
    position: ResearchViewPosition | None = None


class PropertyViewRequest(WireModel):
    wire_version: Literal["1"]
    experiment: ExperimentRevisionRef
    observations: Annotated[
        tuple[ObservationRevisionRef, ...], Field(min_length=1, max_length=128)
    ]
    limit: Annotated[int, Field(ge=1, le=16)] = 16
    position: ResearchViewPosition | None = None


class ObservationSeriesRequest(WireModel):
    wire_version: Literal["1"]
    observation: ObservationRevisionRef
    limit: Annotated[int, Field(ge=1, le=256)] = 256
    position: ResearchViewPosition | None = None
