"""Proposed generation continuity; none of these records grants Runtime acceptance."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, WireModel
from amphora_contracts_search import RngState
from pydantic import Field

from .membership import GenerationIdentity, MembershipPageReference


class PopulationProgress(WireModel):
    evaluations_issued: Annotated[int, Field(ge=0, le=808000)]
    evaluations_terminal: Annotated[int, Field(ge=0, le=808000)]
    attempts_issued: Annotated[int, Field(ge=0, le=9007199254740991)]
    activations_created: Annotated[int, Field(ge=0, le=100000)]
    unchanged_front_generations: Annotated[int, Field(ge=0, le=100)]


class PopulationCheckpoint(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-checkpoint-v1"]
    generation: GenerationIdentity
    selection: ArtifactRef
    rng: RngState
    progress: PopulationProgress


class BirthManifest(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-birth-manifest-v1"]
    generation: GenerationIdentity
    birth_count: Annotated[int, Field(ge=1, le=1000)]
    pages: Annotated[tuple[MembershipPageReference, ...], Field(min_length=1, max_length=512)]


class ProposedSuccessor(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-proposed-successor-v1"]
    generation: GenerationIdentity
    selection: ArtifactRef
    births: ArtifactRef
    cohort: ArtifactRef
    pool: ArtifactRef
    evaluations: ArtifactRef
    rng: RngState
    evaluations_reserved: Annotated[int, Field(ge=0, le=8000)]
    disposition: Literal["evaluate", "duplicate_only", "evaluation_budget"]
