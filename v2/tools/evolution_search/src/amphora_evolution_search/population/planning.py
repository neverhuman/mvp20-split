"""Explicit primary-method numeric fixture policy; no dispatch or budget authority."""

from dataclasses import dataclass

from ..randomness import CounterRandom
from ..ranking import require
from ..variation import ParentVector
from .birth import NumericBirth
from .specification import OriginalPopulation


@dataclass(frozen=True)
class EvaluationCapacity:
    evaluations: int
    attempts: int

    def __post_init__(self):
        require(type(self.evaluations) is int and 0 <= self.evaluations <= 808000, "allocation_evaluations")
        require(type(self.attempts) is int and 0 <= self.attempts <= 9007199254740991, "allocation_attempts")

    def reason(self, cost):
        require(type(cost) is int and 1 <= cost <= 8000, "allocation_cost")
        if self.evaluations < cost:
            return "evaluation_budget"
        if self.attempts < cost:
            return "attempt_budget"
        return None

    def reserve(self, cost):
        require(self.reason(cost) is None, "allocation_exhausted")
        return EvaluationCapacity(self.evaluations - cost, self.attempts - cost)


@dataclass(frozen=True)
class PrimaryBirthBatch:
    original: OriginalPopulation
    generation: int
    births: tuple[NumericBirth, ...]
    rng: CounterRandom
    initial_capacity: EvaluationCapacity
    remaining_capacity: EvaluationCapacity

    @classmethod
    def seed(cls, original, capacity=None):
        budget = original.record.budget
        capacity = EvaluationCapacity(budget.max_evaluations, budget.max_attempts) if capacity is None else capacity
        require(type(capacity) is EvaluationCapacity, "allocation_capacity")
        require(capacity.evaluations <= budget.max_evaluations and capacity.attempts <= budget.max_attempts, "allocation_original_budget")
        return cls._allocate(original, 0, capacity, (), CounterRandom(original.record.seed))

    @classmethod
    def successor(cls, selected, capacity=None):
        require(selected.stop_reason is None, "allocation_stopped_source")
        original = selected.decision.pool.original
        budget, progress = original.record.budget, selected.record.progress
        remaining = EvaluationCapacity(budget.max_evaluations - progress.evaluations_issued,
                                       budget.max_attempts - progress.attempts_issued)
        capacity = remaining if capacity is None else capacity
        require(type(capacity) is EvaluationCapacity and capacity.evaluations <= remaining.evaluations
                and capacity.attempts <= remaining.attempts, "allocation_observed_capacity")
        parents = tuple(ParentVector(b.record.candidate_id, b.record.genes) for b in selected.parents)
        return cls._allocate(original, selected.record.generation.generation + 1, capacity, parents,
                             CounterRandom.from_record(selected.record.rng, expected_seed=original.record.seed))

    @classmethod
    def _allocate(cls, original, generation, capacity, parents, rng):
        require(generation <= original.record.budget.successor_generations, "allocation_generation_budget")
        seen = {parent.genes: parent.candidate_id for parent in parents}
        initial = capacity
        births = []
        cost = len(original.record.method_graph.methods)
        for ordinal in range(original.record.budget.population_size):
            birth = NumericBirth.seed(original, ordinal) if generation == 0 else NumericBirth.vary(original, generation, ordinal, parents, rng)
            rng = CounterRandom(original.record.seed, birth.record.draws.end)
            reason = capacity.reason(cost)
            if birth.record.genes in seen:
                record = birth.record.model_copy(update={"disposition": "duplicate", "reason_code": "duplicate_genes",
                                                         "duplicate_of": seen[birth.record.genes]})
            elif reason is not None:
                record = birth.record.model_copy(update={"disposition": "rejected", "reason_code": reason})
            else:
                record = birth.record
                seen[record.genes] = record.candidate_id
                capacity = capacity.reserve(cost)
            births.append(NumericBirth(original, record))
        return cls(original, generation, tuple(births), rng, initial, capacity)

    @property
    def proposed(self):
        return tuple(b for b in self.births if b.record.disposition == "proposed")

    @property
    def evaluations_reserved(self):
        return self.initial_capacity.evaluations - self.remaining_capacity.evaluations

    @property
    def disposition(self):
        if self.proposed:
            return "evaluate"
        reasons = tuple(b.record.reason_code for b in self.births if b.record.disposition == "rejected")
        if reasons:
            return reasons[0]
        return "duplicate_only"
