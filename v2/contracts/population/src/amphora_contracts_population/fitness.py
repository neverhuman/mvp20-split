"""Fitness records preserve objective evidence and explicit unavailability."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, WireModel
from amphora_contracts_search import ObjectiveValue
from amphora_contracts_tools import ToolBinding
from pydantic import Field

from .membership import GenerationIdentity


class ObjectiveAssessment(WireModel):
    value: ObjectiveValue
    evaluations: Annotated[tuple[Digest, ...], Field(min_length=1, max_length=32)]
    quality: Literal["synthetic", "predicted", "measured", "inferred"]
    confidence: Annotated[float, Field(ge=0, le=1)] | None


class AvailableFitness(WireModel):
    status: Literal["evaluated"]
    objectives: Annotated[tuple[ObjectiveAssessment, ...], Field(min_length=1, max_length=16)]
    constraint_violation: Annotated[float, Field(ge=0)]


class UnavailablePopulationFitness(WireModel):
    status: Literal["unavailable"]
    reason_code: Identifier


class FitnessRecord(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-fitness-v1"]
    generation: GenerationIdentity
    candidate_id: Digest
    assembly: ToolBinding
    policy: ArtifactRef
    evaluation_set_sha256: Digest
    outcome: Annotated[AvailableFitness | UnavailablePopulationFitness, Field(discriminator="status")]


class FitnessPage(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-fitness-page-v1"]
    generation: GenerationIdentity
    ordinal: Annotated[int, Field(ge=0, le=511)]
    records: Annotated[tuple[FitnessRecord, ...], Field(min_length=1, max_length=64)]
