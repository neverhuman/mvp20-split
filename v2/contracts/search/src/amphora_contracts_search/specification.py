"""Wire descriptions of an authorized finite continuous search space."""

from typing import Annotated, Literal

from amphora_contracts_core import (
    ArtifactRef,
    Digest,
    Identifier,
    SchemaRef,
    Scope,
    WireModel,
)
from amphora_contracts_tools import ToolBinding
from pydantic import Field

Count = Annotated[int, Field(ge=0, le=9007199254740991)]
Unit = Annotated[str, Field(min_length=1, max_length=64)]
Probability = Annotated[float, Field(ge=0, le=1)]


class ImplementationPin(WireModel):
    name: Identifier
    version: Annotated[str, Field(min_length=1, max_length=128)]
    sha256: Digest


class NumericVariable(WireModel):
    variable_id: Identifier
    unit: Unit
    lower: Annotated[float, Field(ge=-1e100, le=1e100)]
    upper: Annotated[float, Field(ge=-1e100, le=1e100)]


class NumericObjective(WireModel):
    objective_id: Identifier
    unit: Unit
    direction: Literal["minimize", "maximize"]


class SearchOperators(WireModel):
    selection: Literal["constrained-pareto-feasible-v1"]
    variation: Literal["box-convex-uniform-v1"]
    rng: Literal["sha256-counter-u53-v1"]
    crossover_probability: Probability
    mutation_probability: Probability
    mutation_fraction: Probability


class SearchBudget(WireModel):
    population_size: Annotated[int, Field(ge=1, le=128)]
    max_generations: Annotated[int, Field(ge=0, le=10000)]
    max_evaluations: Annotated[int, Field(ge=0, le=1000000)]
    unchanged_front_limit: Annotated[int, Field(ge=1, le=10000)] | None


class EvaluatorPolicy(WireModel):
    tool: ToolBinding
    constraints: ArtifactRef
    context: Annotated[tuple[ArtifactRef, ...], Field(max_length=32)]
    completion: Literal["all_frozen_members_terminal"]


class SearchSpec(WireModel):
    schema_version: Literal["1"]
    scope: Scope
    search_id: Identifier
    seed: Digest
    representation: SchemaRef
    variables: Annotated[tuple[NumericVariable, ...], Field(min_length=1, max_length=32)]
    objectives: Annotated[tuple[NumericObjective, ...], Field(min_length=1, max_length=16)]
    evaluator: EvaluatorPolicy
    operators: SearchOperators
    budget: SearchBudget
    implementations: Annotated[tuple[ImplementationPin, ...], Field(min_length=1, max_length=32)]
