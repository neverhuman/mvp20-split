"""Closed page/manifest records for retained birth and method evidence."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, WireModel
from pydantic import Field

from .candidates import CandidateBirth
from .evaluations import EvaluationKey, MethodObservation
from .membership import GenerationIdentity, MembershipPageReference


class BirthPage(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-birth-page-v1"]
    generation: GenerationIdentity
    ordinal: Annotated[int, Field(ge=0, le=511)]
    records: Annotated[tuple[CandidateBirth, ...], Field(min_length=1, max_length=64)]


class EvaluationKeyPage(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-evaluation-key-page-v1"]
    generation: GenerationIdentity
    ordinal: Annotated[int, Field(ge=0, le=511)]
    records: Annotated[tuple[EvaluationKey, ...], Field(min_length=1, max_length=64)]


class MethodObservationPage(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-method-observation-page-v1"]
    generation: GenerationIdentity
    ordinal: Annotated[int, Field(ge=0, le=511)]
    records: Annotated[tuple[MethodObservation, ...], Field(min_length=1, max_length=64)]


class EvaluationManifest(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-evaluation-manifest-v1"]
    generation: GenerationIdentity
    membership: ArtifactRef
    evaluation_set_sha256: Digest
    evaluation_count: Annotated[int, Field(ge=0, le=16000)]
    pages: Annotated[tuple[MembershipPageReference, ...], Field(max_length=512)]


class ObservationManifest(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-observation-manifest-v1"]
    generation: GenerationIdentity
    evaluations: ArtifactRef
    evaluation_set_sha256: Digest
    observation_cut_sha256: Digest
    terminal_count: Annotated[int, Field(ge=0, le=16000)]
    pages: Annotated[tuple[MembershipPageReference, ...], Field(max_length=512)]


class FitnessManifest(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-fitness-manifest-v1"]
    generation: GenerationIdentity
    pool: ArtifactRef
    observations: Annotated[tuple[ArtifactRef, ...], Field(max_length=101)]
    member_count: Annotated[int, Field(ge=0, le=2000)]
    pages: Annotated[tuple[MembershipPageReference, ...], Field(max_length=512)]
