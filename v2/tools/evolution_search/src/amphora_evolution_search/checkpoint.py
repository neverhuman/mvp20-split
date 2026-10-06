"""Intrinsic checkpoint consistency, not Artifact retention or Runtime authority."""

import itertools
from dataclasses import dataclass

from amphora_contracts_search import (
    EvaluatedFitness,
    SearchCheckpoint,
    search_checkpoint_schema,
)

from .attempts import validate_attempt, validate_seed_batch
from .evaluations import recompute_selection, validate_evaluations
from .ranking import require
from .specification import OriginalSearch, canonical_bytes


@dataclass(frozen=True)
class CheckpointSnapshot:
    original: OriginalSearch
    record: SearchCheckpoint

    def __post_init__(self):
        checked = SearchCheckpoint.model_validate_json(self.record.model_dump_json())
        object.__setattr__(self, "record", checked)
        self.original.require_binding(checked.specification, checked.specification_sha256)
        self.original.resume_random(checked.rng)
        self._validate_pool()
        attempts = {a.candidate_id: a for a in checked.attempts}
        observations = validate_evaluations(self.original, checked, attempts)
        self._validate_phase(observations)
        self._validate_progress()

    @classmethod
    def decode(cls, original: OriginalSearch, payload: bytes):
        return cls(original, SearchCheckpoint.model_validate_json(payload))

    def encode(self) -> bytes:
        return canonical_bytes(self.record)

    def _validate_pool(self):
        record = self.record
        budget = self.original.record.budget
        require(record.generation <= budget.max_generations, "generation_budget")
        require(len(record.attempts) <= 2 * budget.population_size, "pool_budget")
        by_id = {a.candidate_id: a for a in record.attempts}
        require(len(by_id) == len(record.attempts), "duplicate_attempt")
        slots = {(a.generation, a.ordinal) for a in record.attempts}
        require(len(slots) == len(record.attempts), "duplicate_attempt_slot")
        proposed_genes = [a.genes for a in record.attempts if a.disposition == "proposed"]
        require(len(set(proposed_genes)) == len(proposed_genes), "unmarked_duplicate")
        for attempt in record.attempts:
            validate_attempt(self.original, attempt)
            require(attempt.generation <= record.generation, "future_attempt")
            require(attempt.draws.end <= record.rng.counter, "future_draw")
            for parent in attempt.parents:
                require(parent != attempt.candidate_id, "self_parent")
                if attempt.generation == record.generation:
                    require(parent in by_id, "missing_parent")
                    if record.selection is None:
                        require(parent in record.population, "unselected_parent")
                # Older ancestry can live in the predecessor Artifact chain.
                if parent in by_id:
                    require(by_id[parent].generation < attempt.generation, "parent_generation")
            if attempt.disposition == "duplicate":
                require(attempt.duplicate_of in by_id, "missing_duplicate")
                earlier = by_id[attempt.duplicate_of]
                require((earlier.generation, earlier.ordinal) < (attempt.generation, attempt.ordinal), "duplicate_order")
                require(earlier.genes == attempt.genes and earlier.disposition == "proposed", "duplicate_target")
        current = sorted((a for a in record.attempts if a.generation == record.generation), key=lambda a: a.ordinal)
        ordered = sorted(record.attempts, key=lambda a: (a.generation, a.ordinal))
        require(all(a.draws.end <= b.draws.start for a, b in itertools.pairwise(ordered)), "rng_overlap")
        require(bool(current) and len(current) <= budget.population_size, "generation_membership")
        require([a.ordinal for a in current] == list(range(len(current))), "generation_ordinals")
        require(all(a.draws.end == b.draws.start for a, b in itertools.pairwise(current)), "rng_gap")
        require(current[-1].draws.end == record.rng.counter, "rng_tail")
        if record.generation == 0:
            require(current[0].draws.start == 0, "seed_rng_start")
            validate_seed_batch(self.original, current)
        if record.previous is None:
            require(record.generation == 0, "missing_predecessor")
        else:
            require(record.previous.scope == self.original.record.scope, "predecessor_scope")
            require(record.previous.schema_ref == search_checkpoint_schema(), "predecessor_schema")
        require(len(set(record.population)) == len(record.population), "duplicate_population")
        require(len(record.population) <= budget.population_size, "population_budget")
        require(set(record.population) <= by_id.keys(), "population_membership")

    def _validate_phase(self, observations):
        record = self.record
        require((record.phase == "stopped") == (record.stop_reason is not None), "stop_phase")
        if record.phase == "awaiting_evaluations":
            require(bool(record.pending) and record.selection is None, "awaiting_phase")
        else:
            require(not record.pending, "unfinished_evaluations")
        if record.phase == "ready_to_select":
            require(bool(observations) and record.selection is None, "ready_phase")
        if record.phase == "selected":
            require(record.selection is not None, "missing_selection")
        if record.selection is not None:
            require(record.phase in {"selected", "stopped"}, "premature_selection")
            expected = recompute_selection(self.original, tuple(observations.values()))
            require(record.selection == expected, "selection_receipt")
            require(record.population == expected.selected, "selected_population")
        else:
            # Before selection, population consists only of previously accepted parents.
            attempts = {a.candidate_id: a for a in record.attempts}
            require(all(attempts[c].generation < record.generation for c in record.population), "unselected_population")
            require(all(c in observations and isinstance(observations[c].outcome, EvaluatedFitness)
                        and observations[c].outcome.constraint_violation == 0 for c in record.population), "parent_fitness")
        if record.stop_reason == "no_feasible_candidates":
            require(record.selection is not None and not record.selection.selected, "false_no_feasible")
        elif record.stop_reason == "unavailable_fitness":
            require(any(not isinstance(o.outcome, EvaluatedFitness) for o in observations.values()), "false_unavailable")
        elif record.stop_reason == "generation_budget":
            require(record.selection is not None and record.generation == self.original.record.budget.max_generations, "false_generation_stop")
        elif record.stop_reason == "evaluation_budget":
            require(record.progress.evaluations_issued == self.original.record.budget.max_evaluations, "false_evaluation_stop")
            require(record.progress.evaluations_issued == 0 or record.selection is not None, "unselected_budget_stop")
        elif record.stop_reason == "unchanged_front":
            limit = self.original.record.budget.unchanged_front_limit
            require(record.selection is not None and limit is not None
                    and record.progress.unchanged_front_generations >= limit, "false_stagnation_stop")

    def _validate_progress(self):
        record, budget = self.record, self.original.record.budget
        progress = record.progress
        require(0 <= progress.evaluations_terminal <= progress.evaluations_issued <= budget.max_evaluations, "evaluation_progress")
        require(progress.evaluations_issued - progress.evaluations_terminal == len(record.pending), "pending_progress")
        require(progress.evaluations_terminal >= len(record.observations), "terminal_progress")
        require(progress.generations_completed == record.generation, "generation_progress")
        require(progress.unchanged_front_generations <= progress.generations_completed, "stagnation_progress")
        if record.generation == 0:
            require(progress.evaluations_issued == len(record.pending) + len(record.observations), "seed_progress")
