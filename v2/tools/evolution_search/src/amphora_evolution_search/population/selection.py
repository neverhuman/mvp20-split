"""Whole-pool selection over complete, explicitly bound fitness; no execution writes."""

from dataclasses import dataclass
import hashlib
from functools import cached_property

from amphora_contracts_core import ArtifactRef

from amphora_contracts_population import (
    ExcludedPopulationMember, RankedPopulationMember, PopulationSelectionReceipt,
    membership_manifest_schema, population_record_schema, MembershipPageReference,
)

from ..ranking import ObjectiveSpace, require
from .fitness import BoundFitness
from .membership import GenerationMembership
from .pages import RecordPages
from .specification import canonical
from .evaluations import observation_cut
from .fronts import FitnessFront


@dataclass(frozen=True)
class PopulationSelection:
    pool: GenerationMembership
    fitness: tuple[BoundFitness, ...]

    def __post_init__(self):
        require(self.pool.role == "selection_pool", "selection_pool_role")
        require(type(self.fitness) is tuple and len(self.fitness) == len(self.pool.members), "selection_fitness_coverage")
        by_id = {item.record.candidate_id: item for item in self.fitness}
        require(len(by_id) == len(self.fitness) and set(by_id) == {m.candidate_id for m in self.pool.members},
                "selection_fitness_identity")
        for member in self.pool.members:
            item = by_id[member.candidate_id]
            source = item.evidence.evaluations.membership
            require(source.original == self.pool.original and source.identity.run_id == self.pool.identity.run_id,
                    "selection_fitness_original")
            record = next(m for m in source.members if m.candidate_id == member.candidate_id)
            require(record.birth == member.birth and record.representation == member.representation,
                    "selection_fitness_representation")
            if member.source == "parent":
                require(source.identity.generation < self.pool.identity.generation, "selection_parent_generation")
            else:
                require(source.identity == self.pool.identity, "selection_current_generation")
        object.__setattr__(self, "fitness", tuple(by_id[key] for key in sorted(by_id)))
        self.observations()  # Bound the complete evidence union at construction.

    def decide(self):
        original = self.pool.original.record
        scores = tuple(item.score for item in self.fitness if item.record.outcome.status == "evaluated")
        excluded = tuple(ExcludedPopulationMember(status="excluded", candidate_id=item.record.candidate_id,
            reason_code=item.record.outcome.reason_code) for item in self.fitness if item.record.outcome.status == "unavailable")
        requested = original.budget.population_size
        space = ObjectiveSpace(tuple(binding.objective.direction for binding in original.assembly.objectives))
        selection = space.select_population(scores, min(requested, len(scores))) if scores else None
        selected = selection.selected if selection is not None else ()
        ranks = selection.ranks if selection is not None else ()
        rows = tuple(RankedPopulationMember(status="ranked", candidate_id=rank.candidate_id, front=rank.front,
            boundary=rank.boundary, distance=rank.distance, feasible=rank.feasible,
            selected=rank.candidate_id in selected) for rank in ranks)
        if not selected:
            disposition, stopped = "no_feasible_survivors", True
        elif len(selected) < original.selection.minimum_parents:
            disposition, stopped = "insufficient_eligible_parents", True
        elif len(selected) < requested:
            disposition, stopped = "insufficient_survivors", False
        else:
            disposition, stopped = "selected", False
        members = tuple(sorted((*rows, *excluded), key=lambda row: row.candidate_id))
        cut = observation_cut(self.observations())
        return PopulationDecision(self.pool, requested, selected, members, disposition, stopped, cut)

    def observations(self):
        return self._observations

    @cached_property
    def _observations(self):
        """Each immutable evidence set is visited once, not once per candidate."""
        sources = {}
        for item in self.fitness:
            source = item.evidence
            prior = sources.setdefault(source.evaluations.digest, source)
            require(prior.cut_sha256 == source.cut_sha256, "selection_observation_conflict")
            require(len(sources) <= 101, "selection_evidence_source_bound")
        records = {}
        for source in sources.values():
            for record in source.observations:
                require(records.setdefault(record.evaluation_sha256, record) == record, "selection_observation_conflict")
                require(len(records) <= 16000, "selection_observation_bound")
        return tuple(records[key] for key in sorted(records))

    def front_progress(self, previous_count):
        generation = self.pool.identity.generation
        require(type(previous_count) is int and 0 <= previous_count <= max(0, generation - 1), "front_generation_count")
        if generation == 0:
            return 0
        decision = self.decide()
        by_id = {item.record.candidate_id: item for item in self.fitness}
        parent_ids = tuple(m.candidate_id for m in self.pool.members if m.source == "parent")
        require(bool(parent_ids), "front_parent_membership")
        parents = tuple(by_id[key].score for key in parent_ids)
        require(all(score.eligible and score.violation == 0 for score in parents), "front_parent_fitness")
        current = tuple(by_id[key].score for key in decision.selected)
        directions = tuple(o.objective.direction for o in self.pool.original.record.assembly.objectives)
        return FitnessFront.from_scores(directions, current).unchanged_count(FitnessFront.from_scores(directions, parents), previous_count)


@dataclass(frozen=True)
class PopulationDecision:
    pool: GenerationMembership
    requested: int
    selected: tuple[str, ...]
    members: tuple
    disposition: str
    stopped: bool
    observation_cut_sha256: str

    def pages(self):
        return RecordPages(self.pool.identity, "population.selection-page", self.members).pack()

    def receipt(self, pool, fitness, pages):
        """Bind separately supplied source refs and exact computed rank pages; no I/O."""
        pool = ArtifactRef.model_validate_json(pool.model_dump_json())
        fitness = ArtifactRef.model_validate_json(fitness.model_dump_json())
        require(pool.scope == fitness.scope == self.pool.identity.scope, "selection_source_scope")
        require(pool.schema_ref == membership_manifest_schema()
                and fitness.schema_ref == population_record_schema("population.fitness-manifest"), "selection_source_schema")
        expected = self.pages()
        require(type(pages) is tuple and len(pages) == len(expected), "selection_page_coverage")
        pages = tuple(MembershipPageReference.model_validate_json(r.model_dump_json()) for r in pages)
        require(len({page.artifact.artifact_id for page in pages}) == len(pages), "selection_page_duplicate")
        for reference, page in zip(pages, expected, strict=True):
            raw = canonical(page)
            require(reference.ordinal == page.ordinal and reference.members == len(page.members), "selection_page_count")
            require(reference.artifact.scope == self.pool.identity.scope
                    and reference.artifact.schema_ref == population_record_schema("population.selection-page")
                    and reference.artifact.media_type == "application/json", "selection_page_schema")
            require(reference.artifact.sha256 == hashlib.sha256(raw).hexdigest() and reference.artifact.size_bytes == len(raw),
                    "selection_page_digest")
        record = PopulationSelectionReceipt(schema_version="1", profile="population-selection-receipt-v1",
            generation=self.pool.identity, pool=pool, fitness=fitness, observation_cut_sha256=self.observation_cut_sha256,
            policy=self.pool.original.record.selection, requested=self.requested, selected=self.selected,
            member_count=len(self.members), pages=pages, disposition=self.disposition, stopped=self.stopped)
        require(len(canonical(record)) <= 262144, "selection_receipt_bytes")
        return record

    def verify_receipt(self, record, pool, fitness):
        checked = PopulationSelectionReceipt.model_validate_json(record.model_dump_json())
        require(checked == self.receipt(pool, fitness, checked.pages), "selection_receipt_replay")
