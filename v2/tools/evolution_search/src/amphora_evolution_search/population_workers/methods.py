"""Registered dimensionless numerical fixtures; accepted observations belong to Runtime."""

import math
from dataclasses import dataclass

from amphora_contracts_population import CandidateBirth, MethodBinding, candidate_birth_schema
from amphora_contracts_population_steps import PopulationCandidateContext, population_step_schema
from amphora_contracts_search import NumericObjective, ObjectiveValue

from ..population.birth import NumericBirth
from ..population.retained import PopulationArtifact
from ..ranking import require
from .cohort import PrimaryCohort


@dataclass(frozen=True)
class PrimaryMethod:
    context: PopulationArtifact
    record: PopulationCandidateContext
    cohort: PrimaryCohort
    birth: NumericBirth
    method: MethodBinding
    objective: NumericObjective

    @classmethod
    def load(cls, source, artifacts, binding, runtime=None):
        record = source.decode(PopulationCandidateContext,
            population_step_schema("population-step.candidate-context"), artifacts.scope)
        if record.generation.generation == 0:
            cohort = PrimaryCohort.load(record.specification, record.declarations, artifacts)
        else:
            from .slices import SeedSlices
            parents = artifacts.derivation(source.reference).declaration.inputs
            prepared = tuple(ref for ref in parents if ref.schema_ref == population_step_schema("population-step.prepared"))
            require(len(prepared) == 1, "population_method_successor_prepared")
            loaded = SeedSlices.load(prepared[0], artifacts, runtime)
            require(loaded.prepared.record.specification == record.specification
                    and loaded.prepared.record.declarations == record.declarations,
                    "population_method_successor_sources")
            cohort = loaded.cohort
        require(record.generation == cohort.membership.identity, "population_method_generation")
        require(cohort.membership.by_id.get(record.member.candidate_id) == record.member, "population_method_member")
        birth = NumericBirth(cohort.original, artifacts.read(record.member.birth).decode(
            CandidateBirth, candidate_birth_schema(), artifacts.scope))
        require(birth.record.candidate_id == record.member.candidate_id and birth.record.disposition == "proposed",
                "population_method_birth")
        methods = tuple(method for method in cohort.original.record.method_graph.methods
            if method.tool == binding and method.node_path[-1] == artifacts.attempt.invocation.node_id)
        require(len(methods) == 1, "population_method_occurrence")
        method = methods[0]
        require(method.input_schema == population_step_schema("population-step.candidate-context"), "population_method_input_schema")
        objectives = tuple(objective.objective for objective in cohort.original.record.assembly.objectives
                           if method.method_id in objective.method_ids)
        require(len(objectives) == 1, "population_method_objective_arity")
        objective = objectives[0]
        require(objective.unit in {"1", "dimensionless"} and all(variable.unit in {"1", "dimensionless"}
            for variable in cohort.original.record.variables), "population_method_dimensionless_only")
        return cls(source, record, cohort, birth, method, objective)

    def publish(self, operation, schema, artifacts):
        require(self.method.output_schema == schema, "population_method_output_schema")
        if operation == "evaluate-squares":
            value = math.fsum(gene * gene for gene in self.birth.record.genes)
        elif operation == "evaluate-negative-sum":
            value = -math.fsum(self.birth.record.genes)
        else:
            raise ValueError("unsupported_population_method")
        result = ObjectiveValue(objective_id=self.objective.objective_id, unit=self.objective.unit, value=value)
        original = self.cohort.original.record
        parents = (self.context.reference, self.record.specification,
            self.record.declarations, self.record.member.birth, self.method.conditions,
            original.constraints, original.assembly.policy, original.method_graph.definition,
            *original.context, *original.knowledge)
        contexts = {ref.artifact_id: ref for ref in parents
                    if ref.schema_ref == population_step_schema("population-step.candidate-context")}
        require(len(contexts) == 1 and contexts.get(self.context.reference.artifact_id) == self.context.reference,
                "population_method_context_ambiguity")
        # A collector can recover the exact input from public Data derivation and
        # authenticated Runtime completion, without guessing candidate/page order.
        return artifacts.publish(result, schema, parents, "method/result")
