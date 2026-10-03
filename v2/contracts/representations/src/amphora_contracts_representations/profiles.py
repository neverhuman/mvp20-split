"""Complete transport descriptors; compatibility and digest verification are Data-owned."""

from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, SchemaRef, Scope, WireModel
from pydantic import Field

Label = Annotated[str, Field(min_length=1, max_length=256)]
Labels = Annotated[tuple[Label, ...], Field(min_length=1, max_length=16)]


class EncoderDescriptor(WireModel):
    provider: Identifier
    model: Identifier
    revision: Identifier
    implementation: SchemaRef
    runtime: SchemaRef


class EncodingInputDescriptor(WireModel):
    modality: Identifier
    task: Identifier
    role: Literal["query", "document", "shared"]
    template: SchemaRef
    instructions: Annotated[str, Field(max_length=4096)]
    context_schema: SchemaRef | None


class EncodingPipelineDescriptor(WireModel):
    tokenizer: SchemaRef
    preprocessing: SchemaRef
    chunking: SchemaRef
    truncation: SchemaRef
    pooling: SchemaRef


class VectorSpaceDescriptor(WireModel):
    dimensions: Annotated[int, Field(ge=1, le=4096)]
    dtype: Literal["float32-le"]
    normalization: Literal["none", "l2"]
    metric: Literal["dot", "cosine", "euclidean"]


class EncodingProfile(WireModel):
    wire_version: Literal["1"]
    profile_id: Identifier
    version: Identifier
    encoder: EncoderDescriptor
    inputs: EncodingInputDescriptor
    pipeline: EncodingPipelineDescriptor
    space: VectorSpaceDescriptor
    applicability: Labels
    limitations: Labels
    determinism: Literal["runtime_pinned", "retained_output_only"]


class EncodingProfileRef(WireModel):
    scope: Scope
    profile_id: Identifier
    version: Identifier
    sha256: Digest
