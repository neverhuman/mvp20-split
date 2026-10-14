"""Freeze occurrence membership without fabricating not-yet-produced inputs."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, WireModel
from pydantic import Field

from .membership import GenerationIdentity, MembershipPageReference


class EvaluationSlot(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-evaluation-slot-v1"]
    generation: GenerationIdentity
    candidate_id: Digest
    method_id: Identifier
    occurrence_id: Identifier


class EvaluationSlotPage(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-evaluation-slot-page-v1"]
    generation: GenerationIdentity
    ordinal: Annotated[int, Field(ge=0, le=511)]
    records: Annotated[tuple[EvaluationSlot, ...], Field(min_length=1, max_length=64)]


class EvaluationDeclarationManifest(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-evaluation-declaration-manifest-v1"]
    generation: GenerationIdentity
    membership: ArtifactRef
    slot_set_sha256: Digest
    slot_count: Annotated[int, Field(ge=0, le=8000)]
    pages: Annotated[tuple[MembershipPageReference, ...], Field(max_length=512)]


class EvaluationResolutionManifest(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-evaluation-resolution-manifest-v1"]
    generation: GenerationIdentity
    declarations: ArtifactRef
    evaluations: ArtifactRef
    slot_set_sha256: Digest
    evaluation_set_sha256: Digest
