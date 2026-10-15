"""Reconstruct the complete seed membership before publishing a bounded slice."""

from dataclasses import dataclass

from amphora_contracts_population import (
    BirthManifest, population_record_schema,
)
from amphora_contracts_population_steps import PreparedPopulationGeneration, population_step_schema

from ..population.dispatch import PreparedGeneration
from ..population.pages import RecordPages
from ..ranking import require
from .cohort import PrimaryCohort


@dataclass(frozen=True)
class SeedSlices:
    prepared: PreparedGeneration
    cohort: PrimaryCohort

    @classmethod
    def load(cls, reference, artifacts, runtime=None):
        root = artifacts.read(reference)
        record = root.decode(PreparedPopulationGeneration, population_step_schema("population-step.prepared"), artifacts.scope)
        require(record.generation.run_id == artifacts.attempt.invocation.run_id and record.generation.generation in {0, 1},
                "population_slice_seed_run")
        successor = None
        if record.generation.generation:
            from .successor_source import PreparedSuccessorSource
            successor = PreparedSuccessorSource.load(reference, artifacts, runtime)
        source = PrimaryCohort.load(record.specification, record.declarations, artifacts, successor=successor)
        require(source.membership.identity == record.generation and source.membership_reference == record.cohort,
                "population_slice_membership")
        birth_record = artifacts.read(record.births).decode(BirthManifest,
            population_record_schema("population.birth-manifest"), artifacts.scope)
        require(birth_record.generation == record.generation, "population_slice_birth_generation")
        births = RecordPages.verified(record.generation, "population.birth-page", birth_record.pages,
            tuple(artifacts.read(page.artifact).content for page in birth_record.pages), birth_record.birth_count)
        require(tuple(births.records) == tuple(b.record for b in source.batch.births), "population_slice_birth_replay")
        if successor is not None:
            successor.verify_pool(source, artifacts)
        return cls(PreparedGeneration.verify(root, source.declarations, record.specification, record.cohort,
                                             record.births, record.declarations), source)

    def publish(self, request, artifacts):
        require(request.prepared == self.prepared.artifact.reference, "population_slice_source")
        sliced = self.prepared.slice(request.start_index, request.limit)
        contexts = tuple(artifacts.publish(context, population_step_schema("population-step.candidate-context"),
            (request.prepared, context.specification, context.declarations, context.member.birth, context.member.representation),
            "slice/context/" + context.member.candidate_id) for context in sliced.contexts)
        record = sliced.bind(contexts)
        return artifacts.publish(record, population_step_schema("population-step.member-slice"),
            (request.prepared, *(artifact.reference for artifact in contexts)), "slice/result")
