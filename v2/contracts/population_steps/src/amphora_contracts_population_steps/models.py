"""Reference-backed graph tool transport, separate from retained population records."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, WireModel
from amphora_contracts_population import CandidateMember, GenerationIdentity
from pydantic import Field


class SeedPopulationRequest(WireModel):
    schema_version: Literal["1"]
    specification: ArtifactRef


class PreparedPopulationGeneration(WireModel):
    schema_version: Literal["1"]
    generation: GenerationIdentity
    specification: ArtifactRef
    births: ArtifactRef
    cohort: ArtifactRef
    declarations: ArtifactRef


class PopulationSliceRequest(WireModel):
    schema_version: Literal["1"]
    prepared: ArtifactRef
    start_index: Annotated[int, Field(ge=0, le=1000)]
    limit: Annotated[int, Field(ge=1, le=32)]


class PopulationCandidateContext(WireModel):
    schema_version: Literal["1"]
    generation: GenerationIdentity
    specification: ArtifactRef
    member: CandidateMember
    declarations: ArtifactRef


class PopulationMemberSlice(WireModel):
    schema_version: Literal["1"]
    generation: GenerationIdentity
    prepared: ArtifactRef
    start_index: Annotated[int, Field(ge=0, le=1000)]
    members: Annotated[tuple[ArtifactRef, ...], Field(max_length=32)]
    next_index: Annotated[int, Field(ge=0, le=1000)]
    complete: bool


class SelectPopulationRequest(WireModel):
    schema_version: Literal["1"]
    specification: ArtifactRef
    pool: ArtifactRef
    fitness: ArtifactRef
    resolution: ArtifactRef
    predecessor: ArtifactRef | None


class ProposePopulationSuccessorRequest(WireModel):
    schema_version: Literal["1"]
    specification: ArtifactRef
    checkpoint: ArtifactRef
