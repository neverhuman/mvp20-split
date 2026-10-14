"""Immutable membership page DTOs; Artifact presence/rights are owner checks."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, Scope, WireModel
from pydantic import Field


class GenerationIdentity(WireModel):
    scope: Scope
    run_id: Identifier
    specification_sha256: Digest
    generation: Annotated[int, Field(ge=0, le=100)]
    predecessor: ArtifactRef | None


class CandidateMember(WireModel):
    candidate_id: Digest
    birth: ArtifactRef
    representation: ArtifactRef
    source: Literal["seed", "parent", "offspring"]


class MembershipPage(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-membership-v1"]
    generation: GenerationIdentity
    role: Literal["cohort", "selection_pool"]
    ordinal: Annotated[int, Field(ge=0, le=511)]
    members: Annotated[tuple[CandidateMember, ...], Field(min_length=1, max_length=64)]


class MembershipPageReference(WireModel):
    ordinal: Annotated[int, Field(ge=0, le=511)]
    members: Annotated[int, Field(ge=1, le=64)]
    artifact: ArtifactRef


class MembershipManifest(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-membership-manifest-v1"]
    generation: GenerationIdentity
    role: Literal["cohort", "selection_pool"]
    member_count: Annotated[int, Field(ge=0, le=2000)]
    pages: Annotated[tuple[MembershipPageReference, ...], Field(max_length=512)]
