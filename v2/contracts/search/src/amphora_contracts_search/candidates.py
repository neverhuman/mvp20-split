"""Attempt and evaluation records preserve failure, pending identity and exact evidence."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, Scope, WireModel
from amphora_contracts_tools import ToolBinding
from pydantic import Field

from .specification import Count, EvaluatorPolicy, NumericObjective, Unit


class RngState(WireModel):
    algorithm: Literal["sha256-counter-u53-v1"]
    seed: Digest
    counter: Count


class RngInterval(WireModel):
    start: Count
    end: Count


class CandidateAttempt(WireModel):
    candidate_id: Digest
    generation: Annotated[int, Field(ge=0, le=10000)]
    ordinal: Annotated[int, Field(ge=0, le=255)]
    operator: Literal["seed", "variation"]
    genes: Annotated[tuple[float, ...], Field(min_length=1, max_length=32)]
    parents: Annotated[tuple[Digest, ...], Field(max_length=2)]
    draws: RngInterval
    disposition: Literal["proposed", "rejected", "duplicate"]
    reason_code: Identifier | None
    duplicate_of: Digest | None


class PendingEvaluation(WireModel):
    evaluation_id: Identifier
    candidate_id: Digest
    request_sha256: Digest


class EvaluationRequest(WireModel):
    schema_version: Literal["1"]
    scope: Scope
    evaluation_id: Identifier
    specification_sha256: Digest
    candidate: CandidateAttempt
    objectives: Annotated[tuple[NumericObjective, ...], Field(min_length=1, max_length=16)]
    evaluator: EvaluatorPolicy


class ObjectiveValue(WireModel):
    objective_id: Identifier
    unit: Unit
    value: float


class EvaluatedFitness(WireModel):
    status: Literal["evaluated"]
    evaluator: ToolBinding
    objectives: Annotated[tuple[ObjectiveValue, ...], Field(min_length=1, max_length=16)]
    constraint_violation: Annotated[float, Field(ge=0)]
    constraints_sha256: Digest
    quality: Literal["synthetic", "predicted", "measured"]
    evidence: Annotated[tuple[ArtifactRef, ...], Field(min_length=1, max_length=32)]


class UnavailableFitness(WireModel):
    status: Literal["unknown", "failed", "inapplicable"]
    reason_code: Identifier
    evidence: Annotated[tuple[ArtifactRef, ...], Field(max_length=32)]


class EvaluationObservation(WireModel):
    schema_version: Literal["1"]
    scope: Scope
    evaluation_id: Identifier
    candidate_id: Digest
    request_sha256: Digest
    outcome: Annotated[EvaluatedFitness | UnavailableFitness, Field(discriminator="status")]
