"""Declared identity transports; none confers evaluation reuse or scientific authority."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, Scope, WireModel
from amphora_contracts_research import MaterialStateRevisionRef
from amphora_contracts_tools import ToolBinding
from pydantic import Field


class RepresentationPolicy(WireModel):
    kind: Literal["numeric", "polymer", "sequence"]
    semantic_profile: SchemaRef
    equivalence_profile: SchemaRef


class RepresentationClaim(WireModel):
    scope: Scope
    policy: RepresentationPolicy
    canonical_sha256: Digest
    source: ArtifactRef


class EvaluationMethod(WireModel):
    evaluator: ToolBinding
    method: SchemaRef
    applicability: SchemaRef


class ObjectiveAxis(WireModel):
    objective_id: Identifier
    unit: Annotated[str, Field(min_length=1, max_length=64)]
    direction: Literal["minimize", "maximize"]
    uncertainty_policy: SchemaRef


class EvaluationReusePolicy(WireModel):
    wire_version: Literal["1"]
    reference: SchemaRef
    purpose: Identifier
    representation: RepresentationPolicy
    method: EvaluationMethod
    synthesis_policy: SchemaRef
    objectives: Annotated[tuple[ObjectiveAxis, ...], Field(min_length=1, max_length=16)]
    required_context: Annotated[tuple[Identifier, ...], Field(max_length=32)]
    material_state_required: bool


class NamedEvaluationContext(WireModel):
    name: Identifier
    artifact: ArtifactRef


class EvaluationContext(WireModel):
    scope: Scope
    material_state: MaterialStateRevisionRef | None
    inputs: Annotated[tuple[NamedEvaluationContext, ...], Field(max_length=32)]


class EvaluationIdentityInput(WireModel):
    wire_version: Literal["1"]
    representation: RepresentationClaim
    policy: EvaluationReusePolicy
    context: EvaluationContext


class EvaluationIdentity(WireModel):
    wire_version: Literal["1"]
    authority: Literal["identity_only"]
    algorithm: Literal["research-evaluation-key-v1"]
    sha256: Digest
    source: ArtifactRef
    representation_sha256: Digest
    policy_sha256: Digest
    context_sha256: Digest
