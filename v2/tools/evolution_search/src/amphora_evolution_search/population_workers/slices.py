"""Reconstruct the complete seed membership before publishing a bounded slice."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_population import (
    BirthManifest, EvaluationDeclarationManifest, MembershipManifest,
    PopulationSpecification, candidate_birth_schema, population_record_schema,
    membership_manifest_schema, population_specification_schema,
)
from amphora_contracts_population_steps import PreparedPopulationGeneration, population_step_schema

from ..population.declarations import DeclaredEvaluations
from ..population.dispatch import PreparedGeneration
from ..population.membership import GenerationMembership
from ..population.pages import RecordPages
from ..population.planning import PrimaryBirthBatch
from ..population.specification import OriginalPopulation, canonical
from ..ranking import require


@dataclass(frozen=True)
class SeedSlices:
    prepared: PreparedGeneration

    @classmethod
    def load(cls, reference, artifacts):
        root = artifacts.read(reference)
        record = root.decode(PreparedPopulationGeneration, population_step_schema("population-step.prepared"), artifacts.scope)
        require(record.generation.run_id == artifacts.attempt.invocation.run_id and record.generation.generation == 0,
                "population_slice_seed_run")
        original = OriginalPopulation(artifacts.read(record.specification).decode(PopulationSpecification,
            population_specification_schema(), artifacts.scope))
        require(artifacts.implementation in original.record.implementations, "population_worker_implementation")
        require(original.record.representation == candidate_birth_schema(), "population_representation_not_supported")
        cohort_artifact = artifacts.read(record.cohort)
        cohort_record = cohort_artifact.decode(MembershipManifest, membership_manifest_schema(), artifacts.scope)
        membership = GenerationMembership.verified(original, cohort_artifact.content,
            tuple(artifacts.read(page.artifact).content for page in cohort_record.pages))
        require(membership.identity == record.generation and membership.role == "cohort", "population_slice_membership")
        birth_record = artifacts.read(record.births).decode(BirthManifest,
            population_record_schema("population.birth-manifest"), artifacts.scope)
        require(birth_record.generation == record.generation, "population_slice_birth_generation")
        births = RecordPages.verified(record.generation, "population.birth-page", birth_record.pages,
            tuple(artifacts.read(page.artifact).content for page in birth_record.pages), birth_record.birth_count)
        expected = PrimaryBirthBatch.seed(original)
        require(tuple(births.records) == tuple(b.record for b in expected.births), "population_slice_birth_replay")
        by_id = {b.record.candidate_id: b.record for b in expected.proposed}
        require(set(membership.by_id) == set(by_id), "population_slice_birth_membership")
        for member in membership.members:
            raw = canonical(by_id[member.candidate_id])
            require(member.source == "seed" and member.representation == member.birth
                and member.birth.sha256 == hashlib.sha256(raw).hexdigest() and member.birth.size_bytes == len(raw),
                "population_slice_birth_binding")
        declaration_artifact = artifacts.read(record.declarations)
        declarations_record = declaration_artifact.decode(EvaluationDeclarationManifest,
            population_record_schema("population.evaluation-declarations"), artifacts.scope)
        declarations = DeclaredEvaluations.verified(membership, record.cohort, declaration_artifact,
            tuple(artifacts.read(page.artifact).content for page in declarations_record.pages))
        require(declarations.slots == DeclaredEvaluations.primary(membership).slots, "population_slice_primary_occurrences")
        return cls(PreparedGeneration.verify(root, declarations, record.specification, record.cohort,
                                             record.births, record.declarations))

    def publish(self, request, artifacts):
        require(request.prepared == self.prepared.artifact.reference, "population_slice_source")
        sliced = self.prepared.slice(request.start_index, request.limit)
        contexts = tuple(artifacts.publish(context, population_step_schema("population-step.candidate-context"),
            (request.prepared, context.specification, context.declarations, context.member.birth, context.member.representation),
            "slice/context/" + context.member.candidate_id) for context in sliced.contexts)
        record = sliced.bind(contexts)
        return artifacts.publish(record, population_step_schema("population-step.member-slice"),
            (request.prepared, *(artifact.reference for artifact in contexts)), "slice/result")
