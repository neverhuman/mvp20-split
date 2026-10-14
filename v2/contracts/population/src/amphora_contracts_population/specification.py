"""Additive population specification DTOs; no scheduling or selection behavior."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, Scope, WireModel
from amphora_contracts_search import ImplementationPin, NumericObjective, NumericVariable, SearchOperators
from amphora_contracts_tools import ToolBinding
from pydantic import Field


class MethodBinding(WireModel):
    method_id: Identifier
    node_path: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=16)]
    tool: ToolBinding
    input_schema: SchemaRef
    output_schema: SchemaRef
    required: bool
    conditions: ArtifactRef


class ObjectiveBinding(WireModel):
    objective: NumericObjective
    method_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=8)]


class MethodGraph(WireModel):
    definition: ArtifactRef
    plan_sha256: Digest
    methods: Annotated[tuple[MethodBinding, ...], Field(min_length=1, max_length=8)]


class FitnessAssembly(WireModel):
    tool: ToolBinding
    policy: ArtifactRef
    objectives: Annotated[tuple[ObjectiveBinding, ...], Field(min_length=1, max_length=16)]


class PopulationSelectionPolicy(WireModel):
    completion: Literal["all_required_terminal"] = "all_required_terminal"
    unavailable: Literal["exclude_required_unavailable"] = "exclude_required_unavailable"
    ordering: Literal["constrained-pareto-feasible-v1"] = "constrained-pareto-feasible-v1"
    minimum_parents: Annotated[int, Field(ge=1, le=1000)] = 2
    insufficient: Literal["stop_below_minimum_continue_reduced"] = "stop_below_minimum_continue_reduced"


class PopulationBudget(WireModel):
    population_size: Annotated[int, Field(ge=1, le=1000)]
    successor_generations: Annotated[int, Field(ge=0, le=100)]
    max_evaluations: Annotated[int, Field(ge=0, le=808000)]
    max_attempts: Annotated[int, Field(ge=0, le=9007199254740991)]
    max_activations: Annotated[int, Field(ge=1, le=100000)]
    deadline_seconds: Annotated[int, Field(ge=1, le=86400)]
    dispatch_slice: Annotated[int, Field(ge=1, le=32)]
    active_invocations: Annotated[int, Field(ge=1, le=8)]
    unchanged_front_limit: Annotated[int, Field(ge=1, le=100)] | None


class PopulationSpecification(WireModel):
    schema_version: Literal["1"]
    profile: Literal["numeric-population-v1"]
    scope: Scope
    search_id: Identifier
    revision: Annotated[int, Field(ge=1, le=9007199254740991)]
    seed: Digest
    representation: SchemaRef
    variables: Annotated[tuple[NumericVariable, ...], Field(min_length=1, max_length=32)]
    method_graph: MethodGraph
    assembly: FitnessAssembly
    constraints: ArtifactRef
    context: Annotated[tuple[ArtifactRef, ...], Field(max_length=32)]
    knowledge: Annotated[tuple[ArtifactRef, ...], Field(max_length=32)]
    operators: SearchOperators
    selection: PopulationSelectionPolicy
    budget: PopulationBudget
    implementations: Annotated[tuple[ImplementationPin, ...], Field(min_length=1, max_length=32)]
