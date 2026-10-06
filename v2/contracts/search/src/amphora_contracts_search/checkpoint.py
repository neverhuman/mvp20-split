"""Portable bounded checkpoint DTOs; the tool owns consistency and resume behavior."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, WireModel
from pydantic import Field

from .candidates import (
    CandidateAttempt,
    EvaluationObservation,
    PendingEvaluation,
    RngState,
)
from .specification import Count, SearchSpec


class SelectionRank(WireModel):
    candidate_id: Digest
    front: Annotated[int, Field(ge=0, le=255)]
    boundary: bool
    distance: Annotated[float, Field(ge=0, le=32)]
    feasible: bool


class SelectionReceipt(WireModel):
    policy: Literal["constrained-pareto-feasible-v1"]
    membership_sha256: Digest
    requested: Annotated[int, Field(ge=0, le=128)]
    selected: Annotated[tuple[Digest, ...], Field(max_length=128)]
    ranks: Annotated[tuple[SelectionRank, ...], Field(max_length=256)]
    disposition: Literal["selected", "zero_requested", "no_feasible_candidates", "insufficient_feasible_candidates"]


class SearchProgress(WireModel):
    evaluations_issued: Count
    evaluations_terminal: Count
    generations_completed: Annotated[int, Field(ge=0, le=10000)]
    unchanged_front_generations: Annotated[int, Field(ge=0, le=10000)]


class SearchCheckpoint(WireModel):
    schema_version: Literal["1"]
    specification: SearchSpec
    specification_sha256: Digest
    previous: ArtifactRef | None
    generation: Annotated[int, Field(ge=0, le=10000)]
    phase: Literal["awaiting_evaluations", "ready_to_select", "selected", "stopped"]
    rng: RngState
    attempts: Annotated[tuple[CandidateAttempt, ...], Field(min_length=1, max_length=256)]
    population: Annotated[tuple[Digest, ...], Field(max_length=128)]
    pending: Annotated[tuple[PendingEvaluation, ...], Field(max_length=256)]
    observations: Annotated[tuple[EvaluationObservation, ...], Field(max_length=256)]
    selection: SelectionReceipt | None
    progress: SearchProgress
    stop_reason: Literal["generation_budget", "evaluation_budget", "unchanged_front", "no_feasible_candidates", "unavailable_fitness"] | None
