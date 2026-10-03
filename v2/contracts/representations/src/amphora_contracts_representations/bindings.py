"""Source-specific requests/results; no public vector-cache lookup or supplied vector authority."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, Scope, WireModel
from amphora_contracts_evidence import SourceSpan
from pydantic import Field

from .profiles import EncodingProfileRef


class EncodeSourceRequest(WireModel):
    wire_version: Literal["1"]
    encoding_id: Identifier
    profile: EncodingProfileRef
    source: SourceSpan


class RepresentationVector(WireModel):
    """Retained Artifact content; Data verifies bytes, digest and complete profile."""

    wire_version: Literal["1"]
    profile: EncodingProfileRef
    input_sha256: Digest
    context_sha256: Digest | None
    dimensions: Annotated[int, Field(ge=1, le=4096)]
    dtype: Literal["float32-le"]
    payload_hex: Annotated[str, Field(min_length=8, max_length=32768, pattern=r"^(?:[0-9a-f]{8})+$")]
    payload_sha256: Digest


class RepresentationBindingRef(WireModel):
    scope: Scope
    binding_id: Identifier
    sha256: Digest


class RepresentationBinding(WireModel):
    wire_version: Literal["1"]
    reference: RepresentationBindingRef
    profile: EncodingProfileRef
    source: SourceSpan
    vector: ArtifactRef


class EncodingPending(WireModel):
    state: Literal["pending"]


class EncodingPublished(WireModel):
    state: Literal["published"]
    binding: RepresentationBinding


class EncodingStatus(WireModel):
    wire_version: Literal["1"]
    request: EncodeSourceRequest
    actor_id: Identifier
    outcome: Annotated[EncodingPending | EncodingPublished, Field(discriminator="state")]
