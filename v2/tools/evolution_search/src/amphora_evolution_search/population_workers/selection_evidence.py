"""Complete immutable pool evidence and cumulative checkpoint progress."""
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from amphora_contracts_population import (
    EvaluationManifest, EvaluationResolutionManifest, FitnessManifest, MembershipManifest,
    ObservationManifest, PopulationProgress, membership_manifest_schema, population_record_schema,
)
from ..population.closure import GenerationPageClosure
from ..population.dispatch import PreparedGeneration
from ..population.membership import GenerationMembership
from ..population.planning import PrimaryBirthBatch
from ..population.retained import PopulationArtifact, RetainedEvaluations, RetainedFitness, RetainedObservations
from ..population.specification import OriginalPopulation
from ..ranking import require
from .collection import prepared_pages
from .method_plan import payload_schema
from .payloads import CollectedPrimaryGeneration
from .slices import SeedSlices

if TYPE_CHECKING:
    from .successor_source import PreparedSuccessorSource


@dataclass(frozen=True)
class SelectionEvidence:
    original: OriginalPopulation
    prepared: PreparedGeneration
    evaluations: RetainedEvaluations
    fitness: RetainedFitness
    pages: tuple[PopulationArtifact, ...]
    observations: tuple[RetainedObservations, ...]
    successor: PreparedSuccessorSource | None

    @classmethod
    def load(cls, request, original, record, collection_request, artifacts, runtime=None):
        collected = artifacts.read(record.collected).decode(CollectedPrimaryGeneration,
            payload_schema(CollectedPrimaryGeneration, "population-worker.collected"), artifacts.scope)
        reconstructed = SeedSlices.load(collected.prepared, artifacts, runtime)
        prepared = reconstructed.prepared
        membership = prepared.declarations.membership
        successor = reconstructed.successor
        require(membership.original == original and membership.identity == record.generation
                and collected.generation == record.generation and collected.specification == request.specification
                and collected.resolution == request.resolution and collection_request.prepared == collected.prepared
                and collected.cohort == prepared.record.cohort and collected.declarations == prepared.record.declarations
                and request.predecessor == record.generation.predecessor,
                "selection_evidence_generation")
        pool_artifact = artifacts.read(request.pool)
        pool_record = pool_artifact.decode(MembershipManifest, membership_manifest_schema(), artifacts.scope)
        pool_pages = tuple(artifacts.read(page.artifact) for page in pool_record.pages)
        pool = GenerationMembership.verified(original, pool_artifact.content, tuple(page.content for page in pool_pages))
        parents = () if successor is None else tuple(successor.selected.decision.pool.by_id[key].model_copy(update={"source": "parent"})
            for key in successor.selected.decision.selected)
        expected = tuple(sorted((*parents, *membership.members), key=lambda member: member.candidate_id))
        require(pool.identity == membership.identity and pool.role == "selection_pool" and pool.members == expected,
                "selection_evidence_complete_pool")
        evaluation = artifacts.read(collected.evaluations)
        evaluation_record = evaluation.decode(EvaluationManifest, population_record_schema("population.evaluation-manifest"), artifacts.scope)
        key_pages = tuple(artifacts.read(page.artifact) for page in evaluation_record.pages)
        retained = RetainedEvaluations.verify(membership, collected.cohort, evaluation, tuple(page.content for page in key_pages))
        resolution = artifacts.read(request.resolution).decode(EvaluationResolutionManifest,
            population_record_schema("population.evaluation-resolution"), artifacts.scope)
        prepared.declarations.verify_resolution(prepared.record.declarations, collected.evaluations, resolution, retained.frozen)
        observations = artifacts.read(collected.observations)
        observation_record = observations.decode(ObservationManifest, population_record_schema("population.observation-manifest"), artifacts.scope)
        observation_pages = tuple(artifacts.read(page.artifact) for page in observation_record.pages)
        evidence = retained.observations(observations, tuple(page.content for page in observation_pages))
        sources = (*(() if successor is None else successor.observations), evidence)
        fitness = artifacts.read(request.fitness)
        fitness_record = fitness.decode(FitnessManifest, population_record_schema("population.fitness-manifest"), artifacts.scope)
        fitness_pages = tuple(artifacts.read(page.artifact) for page in fitness_record.pages)
        selection = RetainedFitness.verify(pool, request.pool, fitness, tuple(page.content for page in fitness_pages), sources)
        previous_pages = () if successor is None else successor.source_pages
        pages = (*previous_pages, *prepared_pages(prepared, artifacts), *pool_pages, *key_pages, *observation_pages, *fitness_pages)
        GenerationPageClosure.verify(record.generation, pages)
        return cls(original, prepared, retained, selection, pages, sources, successor)

    @property
    def rng(self):
        return (PrimaryBirthBatch.seed(self.original).rng if self.successor is None else self.successor.batch.rng).to_record()

    def progress(self, counter):
        previous = None if self.successor is None else self.successor.selected.record.progress
        logical = len(self.evaluations.frozen.keys) + (0 if previous is None else previous.evaluations_issued)
        require(logical <= self.original.record.budget.max_evaluations, "selection_cumulative_evaluation_budget")
        require(previous is None or (previous.attempts_issued <= counter.attempts_issued
            and previous.activations_created <= counter.activations_created), "selection_cumulative_work_regressed")
        unchanged = self.fitness.selection.front_progress(0 if previous is None else previous.unchanged_front_generations)
        return PopulationProgress(evaluations_issued=logical, evaluations_terminal=logical,
            attempts_issued=counter.attempts_issued, activations_created=counter.activations_created,
            unchanged_front_generations=unchanged)
