"""Owner fitness projections preserve declared identity without authorizing reuse."""
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, Scope, WireModel
from amphora_contracts_evaluation_identity import EvaluationIdentity, EvaluationIdentityInput, EvaluationReusePolicy
from amphora_contracts_research import (
    CandidateRevision, CandidateRevisionRef, EligibilityDecision, InterpretationRef,
    MeasurementQuantity, ObservationRevisionRef, ObservationUseProjection, ScientificDecisionRef, SynthesisDecision,
)
from pydantic import Field


class FitnessProfileRef(WireModel):
    scope: Scope
    policy: SchemaRef


class FitnessProfile(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic"]
    scope: Scope
    evaluation: EvaluationReusePolicy
    observation_use: SchemaRef
    synthesis_required: bool


class FitnessRequest(WireModel):
    wire_version: Literal["1"]
    fitness_id: Identifier
    profile: FitnessProfileRef
    candidate: CandidateRevisionRef
    interpretation: InterpretationRef
    eligibility: ScientificDecisionRef
    synthesis: ScientificDecisionRef
    declared_identity: ArtifactRef


class FitnessSelection(WireModel):
    scope: Scope
    fitness_id: Identifier


class FitnessRef(FitnessSelection):
    sha256: Digest


class FitnessEvidenceRecord(WireModel):
    candidate: CandidateRevision
    interpretation: ObservationUseProjection
    eligibility: EligibilityDecision
    synthesis: SynthesisDecision


class FitnessAxisRecord(WireModel):
    objective_id: Identifier
    status: Literal["available", "unavailable"]
    value: MeasurementQuantity | None
    observations: Annotated[tuple[ObservationRevisionRef, ...], Field(max_length=1024)]
    reasons: Annotated[tuple[Identifier, ...], Field(max_length=64)]


class FitnessProjection(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic_owner_projection"]
    reuse_authority: Literal["none"]
    reference: FitnessRef
    actor_id: Identifier
    profile: FitnessProfile
    request: FitnessRequest
    declared_identity: EvaluationIdentityInput
    identity: EvaluationIdentity
    evidence: FitnessEvidenceRecord
    axes: Annotated[tuple[FitnessAxisRecord, ...], Field(min_length=1, max_length=16)]
    disposition: Literal["ready", "unavailable", "excluded"]
    synthesis_status: Literal["eligible", "unknown", "blocked"]
    focus: Annotated[tuple[Identifier, ...], Field(max_length=4096)]
    sources: Annotated[tuple[ArtifactRef, ...], Field(min_length=1, max_length=128)]
