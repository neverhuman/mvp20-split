"""Generation transport shapes; Data owns admission, verification and publication."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, SchemaRef, Scope, WireModel
from pydantic import Field

from .bindings import RepresentationBinding, RepresentationBindingRef
from .profiles import EncodingProfileRef


class IndexGenerationRef(WireModel):
    scope: Scope
    corpus_id: Identifier
    generation_id: Identifier
    sha256: Digest


class BuildIndexGeneration(WireModel):
    wire_version: Literal["1"]
    corpus_id: Identifier
    generation_id: Identifier
    profile: EncodingProfileRef
    bindings: Annotated[tuple[RepresentationBindingRef, ...], Field(min_length=1, max_length=256)]
    expected_head: IndexGenerationRef | None


class IndexManifest(WireModel):
    wire_version: Literal["1"]
    scope: Scope
    profile: EncodingProfileRef
    bindings: Annotated[tuple[RepresentationBinding, ...], Field(min_length=1, max_length=256)]
    watermark: Digest


class IndexGeneration(WireModel):
    wire_version: Literal["1"]
    reference: IndexGenerationRef
    actor_id: Identifier
    manifest: IndexManifest
    expected_head: IndexGenerationRef | None
    backend_profile: SchemaRef


class IndexGenerationStatus(WireModel):
    wire_version: Literal["1"]
    generation: IndexGeneration
    state: Literal["prepared", "building", "verified", "published", "failed", "abandoned"]
