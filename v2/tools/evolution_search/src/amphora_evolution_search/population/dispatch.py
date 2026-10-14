"""Materialize bounded candidate contexts; Runtime alone dispatches the method graph."""

from dataclasses import dataclass

from amphora_contracts_population import membership_manifest_schema, population_record_schema, population_specification_schema
from amphora_contracts_population_steps import (
    PopulationCandidateContext, PopulationMemberSlice, PreparedPopulationGeneration, population_step_schema,
)

from ..ranking import require
from .declarations import DeclaredEvaluations
from .retained import PopulationArtifact
from .specification import canonical


@dataclass(frozen=True)
class PreparedGeneration:
    artifact: PopulationArtifact
    record: PreparedPopulationGeneration
    declarations: DeclaredEvaluations

    @classmethod
    def verify(cls, artifact, declarations, specification_reference, cohort_reference, birth_reference, declaration_reference):
        identity = declarations.membership.identity
        record = artifact.decode(PreparedPopulationGeneration, population_step_schema("population-step.prepared"), identity.scope)
        require(record.generation == identity and record.specification == specification_reference
                and record.cohort == cohort_reference and record.births == birth_reference
                and record.declarations == declaration_reference, "prepared_generation_sources")
        for reference, schema in ((specification_reference, population_specification_schema()),
                                  (cohort_reference, membership_manifest_schema()),
                                  (birth_reference, population_record_schema("population.birth-manifest")),
                                  (declaration_reference, population_record_schema("population.evaluation-declarations"))):
            require(reference.scope == identity.scope and reference.schema_ref == schema and reference.media_type == "application/json",
                    "prepared_generation_reference")
        return cls(artifact, record, declarations)

    def slice(self, start, limit):
        members = self.declarations.membership.members
        require(type(start) is int and 0 <= start <= len(members), "dispatch_start")
        require(type(limit) is int and 1 <= limit <= self.declarations.membership.original.record.budget.dispatch_slice,
                "dispatch_slice_budget")
        end = min(start + limit, len(members))
        contexts = tuple(PopulationCandidateContext(schema_version="1", generation=self.record.generation,
            specification=self.record.specification, member=member, declarations=self.record.declarations)
            for member in members[start:end])
        require(all(len(canonical(c)) <= 8192 for c in contexts), "dispatch_context_bytes")
        return CandidateSlice(self, start, end, end == len(members), contexts)


@dataclass(frozen=True)
class CandidateSlice:
    source: PreparedGeneration
    start: int
    next_index: int
    complete: bool
    contexts: tuple[PopulationCandidateContext, ...]

    def bind(self, artifacts):
        require(type(artifacts) is tuple and len(artifacts) == len(self.contexts), "dispatch_context_coverage")
        require(len({a.reference.artifact_id for a in artifacts}) == len(artifacts), "dispatch_context_duplicate")
        for artifact, context in zip(artifacts, self.contexts, strict=True):
            checked = artifact.decode(PopulationCandidateContext, population_step_schema("population-step.candidate-context"),
                                      self.source.record.generation.scope)
            require(checked == context, "dispatch_context_binding")
        record = PopulationMemberSlice(schema_version="1", generation=self.source.record.generation,
            prepared=self.source.artifact.reference, start_index=self.start, members=tuple(a.reference for a in artifacts),
            next_index=self.next_index, complete=self.complete)
        require(len(canonical(record)) <= 262144, "dispatch_slice_bytes")
        return record

    def verify(self, record, artifacts):
        checked = PopulationMemberSlice.model_validate_json(record.model_dump_json())
        require(checked == self.bind(artifacts), "dispatch_slice_replay")
