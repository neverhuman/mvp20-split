"""Selection pages carry full ranks/exclusions; a receipt never ranks a UI page."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, WireModel
from pydantic import Field

from .membership import GenerationIdentity, MembershipPageReference
from .specification import PopulationSelectionPolicy


class RankedPopulationMember(WireModel):
    status: Literal["ranked"]
    candidate_id: Digest
    front: Annotated[int, Field(ge=0, le=1999)]
    boundary: bool
    distance: Annotated[float, Field(ge=0, le=32)]
    feasible: bool
    selected: bool


class ExcludedPopulationMember(WireModel):
    status: Literal["excluded"]
    candidate_id: Digest
    reason_code: Identifier


class SelectionPage(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-selection-page-v1"]
    generation: GenerationIdentity
    ordinal: Annotated[int, Field(ge=0, le=511)]
    members: Annotated[tuple[Annotated[RankedPopulationMember | ExcludedPopulationMember,
        Field(discriminator="status")], ...], Field(min_length=1, max_length=64)]


class PopulationSelectionReceipt(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-selection-receipt-v1"]
    generation: GenerationIdentity
    pool: ArtifactRef
    fitness: ArtifactRef
    observation_cut_sha256: Digest
    policy: PopulationSelectionPolicy
    requested: Annotated[int, Field(ge=1, le=1000)]
    selected: Annotated[tuple[Digest, ...], Field(max_length=1000)]
    member_count: Annotated[int, Field(ge=0, le=2000)]
    pages: Annotated[tuple[MembershipPageReference, ...], Field(max_length=512)]
    disposition: Literal["selected", "insufficient_survivors", "no_feasible_survivors", "insufficient_eligible_parents"]
    stopped: bool
