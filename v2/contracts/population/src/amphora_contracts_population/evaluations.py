"""Named method evaluations; retries remain Runtime attempts under one key."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, WireModel
from amphora_contracts_tools import ToolBinding
from pydantic import Field

from .membership import GenerationIdentity


class EvaluationKey(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-evaluation-key-v1"]
    generation: GenerationIdentity
    candidate_id: Digest
    occurrence_id: Identifier
    method_id: Identifier
    tool: ToolBinding
    material: ArtifactRef
    inputs: Annotated[tuple[ArtifactRef, ...], Field(min_length=1, max_length=32)]
    conditions: ArtifactRef
    objective_policy_sha256: Digest


class ExecutionPointer(WireModel):
    run_id: Identifier
    activation_id: Identifier
    invocation_id: Identifier
    attempt_id: Identifier
    completion_id: Identifier


class MethodOutput(WireModel):
    port: Identifier
    artifact: ArtifactRef


class EvaluatedMethod(WireModel):
    status: Literal["evaluated"]
    producer: ExecutionPointer
    outputs: Annotated[tuple[MethodOutput, ...], Field(min_length=1, max_length=32)]


class UnavailableMethod(WireModel):
    status: Literal["failed", "cancelled", "unknown", "inapplicable"]
    reason_code: Identifier
    producer: ExecutionPointer | None
    evidence: Annotated[tuple[ArtifactRef, ...], Field(max_length=32)]


class MethodObservation(WireModel):
    schema_version: Literal["1"]
    profile: Literal["population-method-observation-v1"]
    key: EvaluationKey
    evaluation_sha256: Digest
    outcome: Annotated[EvaluatedMethod | UnavailableMethod, Field(discriminator="status")]
