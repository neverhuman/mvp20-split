"""Versioned planning transport records; no authorization or provider behavior."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SafePositiveInt, SchemaRef, Scope, WireModel
from pydantic import Field

ProposalAction = Literal["abstain", "request_evidence", "propose_knowledge_change", "propose_campaign"]
TokenCount = Annotated[int, Field(ge=0, le=16777216)]
TokenLimit = Annotated[int, Field(ge=1, le=16777216)]


class ModelBinding(WireModel):
    provider_id: Identifier
    model_id: Identifier
    model_revision: Identifier
    configuration: ArtifactRef
    tokenizer: SchemaRef
    context_window_tokens: TokenLimit


class CallLimits(WireModel):
    max_input_tokens: TokenLimit
    max_output_tokens: TokenLimit
    max_attempts: Annotated[int, Field(ge=1, le=16)]
    total_tokens: Annotated[int, Field(ge=1, le=268435456)]
    total_accounting_units: SafePositiveInt
    accounting_unit: Identifier


class ContextEntry(WireModel):
    artifact: ArtifactRef
    role: Literal["constraint", "source", "capability", "knowledge", "result"]
    required: bool


class ContextOmission(WireModel):
    artifact: ArtifactRef
    reason: Literal["budget", "not_relevant", "unavailable", "not_authorized"]


class ContextManifest(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    objective: ArtifactRef
    prompt: ArtifactRef
    policy: ArtifactRef
    model: ModelBinding
    entries: Annotated[tuple[ContextEntry, ...], Field(max_length=128)]
    omissions: Annotated[tuple[ContextOmission, ...], Field(max_length=128)]
    allowed_actions: Annotated[tuple[ProposalAction, ...], Field(min_length=1, max_length=4)]
    output_schema: SchemaRef
    limits: CallLimits
