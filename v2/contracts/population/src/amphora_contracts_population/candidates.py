"""Candidate birth identity is separate from membership and execution attempts."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, Scope, WireModel
from amphora_contracts_search import RngInterval
from pydantic import Field


class CandidateBirth(WireModel):
    schema_version: Literal["1"]
    profile: Literal["numeric-population-birth-v1"]
    scope: Scope
    specification_sha256: Digest
    candidate_id: Digest
    generation: Annotated[int, Field(ge=0, le=100)]
    ordinal: Annotated[int, Field(ge=0, le=999)]
    operator: Literal["seed", "variation"]
    genes: Annotated[tuple[float, ...], Field(min_length=1, max_length=32)]
    parents: Annotated[tuple[Digest, ...], Field(max_length=2)]
    draws: RngInterval
    disposition: Literal["proposed", "rejected", "duplicate"]
    reason_code: Identifier | None
    duplicate_of: Digest | None
