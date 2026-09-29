"""Boundary validation/serialization only; stage algorithms belong to isolated tools."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Name = Annotated[str, Field(min_length=1, max_length=96, pattern=r"^[a-zA-Z0-9_.:-]+$")]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Seed = Annotated[int, Field(ge=0, le=1_100_000)]
Generation = Annotated[int, Field(ge=0, le=8)]


class Record(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True, allow_inf_nan=False)


class SourcePins(Record):
    cli: Digest
    engine: Digest
    ranking: Digest


class SolverConfig(Record):
    schema_version: Literal["1"] = "1"
    source_pins: SourcePins
    seed: Annotated[int, Field(ge=0, le=1_000_000)]
    population: Annotated[int, Field(ge=1, le=8)]
    generations: Generation
    reject_mutation_seeds: Annotated[tuple[Seed, ...], Field(max_length=72)] = ()
    fail_scoring_seeds: Annotated[tuple[Seed, ...], Field(max_length=72)] = ()
    error_modules: Annotated[tuple[Name, ...], Field(max_length=32)] = ()


class Candidate(Record):
    candidate_id: Name
    parent_ids: Annotated[tuple[Name, ...], Field(max_length=1)]
    generation: Generation
    proposal_index: Annotated[int, Field(ge=0, le=7)]
    proposal_seed: Seed
    scoring_seed: Seed
    structure: Literal["unchanged-reference-structure"] = "unchanged-reference-structure"


class ScoreRequest(Record):
    schema_version: Literal["1"] = "1"
    source_pins: SourcePins
    candidate: Candidate
    fail_scoring: bool = False
    error_modules: Annotated[tuple[Name, ...], Field(max_length=32)] = ()


class ModuleEnvelope(Record):
    module_id: Name
    status: Literal["SYNTHETIC", "ERROR"]
    authority: Literal["NO_AUTHORITY"] = "NO_AUTHORITY"


class ScoreResult(Record):
    schema_version: Literal["1"] = "1"
    candidate: Candidate
    modules: Annotated[tuple[ModuleEnvelope, ...], Field(min_length=1, max_length=32)]
    ranked: Literal[False] = False
    eligible_objectives: Literal[0] = 0
    display_score: Literal[0] = 0


class Rejection(Record):
    generation: Generation
    proposal_index: Annotated[int, Field(ge=0, le=7)]
    proposal_seed: Seed
    parent_id: Name
    reason_code: Literal["synthetic_mutation_rejected"] = "synthetic_mutation_rejected"


class Checkpoint(Record):
    generation: Generation
    current_ids: Annotated[tuple[Name, ...], Field(max_length=8)]
    cumulative_ids: Annotated[tuple[Name, ...], Field(max_length=72)]
    failed_ids: Annotated[tuple[Name, ...], Field(max_length=8)]
    rejection_seeds: Annotated[tuple[Seed, ...], Field(max_length=8)]


class SolverState(Record):
    schema_version: Literal["1"] = "1"
    config: SolverConfig
    generation: Annotated[int, Field(ge=-1, le=8)]
    current: Annotated[tuple[ScoreResult, ...], Field(max_length=8)]
    cumulative: Annotated[tuple[ScoreResult, ...], Field(max_length=72)]
    checkpoints: Annotated[tuple[Checkpoint, ...], Field(max_length=9)]


class Selection(Record):
    schema_version: Literal["1"] = "1"
    state: SolverState
    parents: Annotated[tuple[Candidate, ...], Field(min_length=1, max_length=8)]
    used_fallback: bool


class ProposalBatch(Record):
    schema_version: Literal["1"] = "1"
    state: SolverState
    generation: Generation
    candidates: Annotated[tuple[ScoreRequest, ...], Field(max_length=8)]
    rejections: Annotated[tuple[Rejection, ...], Field(max_length=8)]


class MissingResult(Record):
    kind: Literal["missing"]
    member_id: Name
    reason_code: Name


class RetainInput(Record):
    schema_version: Literal["1"] = "1"
    batch: ProposalBatch
    results: Annotated[tuple[ScoreResult | MissingResult, ...], Field(max_length=8)]
