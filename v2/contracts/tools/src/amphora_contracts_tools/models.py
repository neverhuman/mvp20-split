"""Tool payloads remain artifact/schema bound; success is not scientific promotion."""

from typing import Annotated, Literal

from amphora_contracts_core import (
    ArtifactRef,
    Digest,
    Identifier,
    SafePositiveInt,
    SchemaRef,
    Scope,
    WireModel,
)
from pydantic import Field


class ToolBinding(WireModel):
    capability_id: Identifier
    release: Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")]
    image_sha256: Digest
    contract_version: Literal["1"]


class Port(WireModel):
    name: Identifier
    schema_ref: SchemaRef
    representation: Identifier
    unit: Annotated[str, Field(min_length=1, max_length=64)]
    required: bool = True


class ToolDescriptor(WireModel):
    schema_version: Literal["1"]
    binding: ToolBinding
    purpose: Annotated[str, Field(min_length=1, max_length=1024)]
    applicability: Annotated[tuple[str, ...], Field(min_length=1, max_length=64)]
    inputs: Annotated[tuple[Port, ...], Field(max_length=64)]
    outputs: Annotated[tuple[Port, ...], Field(max_length=64)]
    side_effects: Literal["pure", "idempotent", "external"]
    checkpoint_schema: SchemaRef | None = None


class InputBinding(WireModel):
    port: Identifier
    artifact: ArtifactRef


class Invocation(WireModel):
    schema_version: Literal["1"]
    scope: Scope
    run_id: Identifier
    node_id: Identifier
    activation_id: Identifier
    invocation_id: Identifier
    attempt_id: Identifier
    fence: SafePositiveInt
    tool: ToolBinding
    inputs: Annotated[tuple[InputBinding, ...], Field(max_length=64)]
    checkpoint: ArtifactRef | None = None
    timeout_seconds: Annotated[int, Field(ge=1, le=86400)]
    grant_id: Identifier


class Succeeded(WireModel):
    status: Literal["succeeded"]
    outputs: Annotated[tuple[InputBinding, ...], Field(min_length=1, max_length=64)]
    checkpoint: ArtifactRef | None = None


class Abstained(WireModel):
    status: Literal["abstained"]
    reason_code: Identifier


class Failed(WireModel):
    status: Literal["failed"]
    reason_code: Identifier
    retryable: bool


class Uncertain(WireModel):
    status: Literal["uncertain_external_effect"]
    operation_id: Identifier
    reason_code: Identifier


Outcome = Annotated[Succeeded | Abstained | Failed | Uncertain, Field(discriminator="status")]


class Completion(WireModel):
    schema_version: Literal["1"]
    invocation_id: Identifier
    attempt_id: Identifier
    fence: SafePositiveInt
    outcome: Outcome
