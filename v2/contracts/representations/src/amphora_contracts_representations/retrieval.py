"""Pinned retrieval transport; owner records and current rights supply authority."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, WireModel
from pydantic import Field

from .bindings import RepresentationBinding, RepresentationBindingRef
from .generations import IndexGenerationRef


class RetrievalPolicy(WireModel):
    format: Literal["data.exact-dot-ranking.v1"]
    top_k: Annotated[int, Field(strict=True, ge=1, le=256)]
    bindings: Annotated[tuple[RepresentationBindingRef, ...], Field(max_length=256)] | None
    metric: Literal["dot"]
    order: Literal["score_desc_binding_asc"]
    quality_filter: Literal["none"]


class RetrieveRepresentations(WireModel):
    wire_version: Literal["1"]
    retrieval_id: Identifier
    generation: IndexGenerationRef
    query: RepresentationBindingRef
    policy: RetrievalPolicy


class RetrievalMatch(WireModel):
    binding: RepresentationBinding
    score: Annotated[float, Field(strict=True, allow_inf_nan=False)]


class RetrievalRecord(WireModel):
    wire_version: Literal["1"]
    retrieval_id: Identifier
    actor_id: Identifier
    generation: IndexGenerationRef
    query: RepresentationBinding
    policy: RetrievalPolicy
    query_sha256: Digest
    matches: Annotated[tuple[RetrievalMatch, ...], Field(max_length=256)]
    sha256: Digest
