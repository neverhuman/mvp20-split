"""One bounded box-variation attempt with an explicit fixed draw schedule."""

import re
from dataclasses import dataclass

from .randomness import CounterRandom
from .ranking import require
from .specification import OriginalSearch


@dataclass(frozen=True)
class ParentVector:
    candidate_id: str
    genes: tuple[float, ...]


@dataclass(frozen=True)
class VariationDraw:
    genes: tuple[float, ...]
    parents: tuple[str, ...]
    before: CounterRandom
    after: CounterRandom


@dataclass(frozen=True)
class BoxVariation:
    original: OriginalSearch

    def draw(self, parents: tuple[ParentVector, ...], rng: CounterRandom) -> VariationDraw:
        require(type(parents) is tuple and 1 <= len(parents) <= self.original.record.budget.population_size, "variation_population")
        require(all(type(p) is ParentVector and type(p.candidate_id) is str
                    and re.fullmatch(r"[0-9a-f]{64}", p.candidate_id) for p in parents), "variation_parent_identity")
        require(len({p.candidate_id for p in parents}) == len(parents), "variation_duplicate_parent")
        require(all(self.original.box.contains(p.genes) for p in parents), "variation_parent_bounds")
        require(rng.seed == self.original.record.seed, "variation_seed")
        before = rng
        first, rng = rng.draw()
        second, rng = rng.draw()
        crossing, rng = rng.draw()
        left, right = parents[int(first * len(parents))], parents[int(second * len(parents))]
        policy = self.original.record.operators
        genes = []
        for a, b, (low, high) in zip(left.genes, right.genes, self.original.box.bounds, strict=True):
            blend, rng = rng.draw()
            mutate, rng = rng.draw()
            offset, rng = rng.draw()
            value = a
            if crossing < policy.crossover_probability:
                value = blend * a + (1 - blend) * b
            if mutate < policy.mutation_probability:
                value += (2 * offset - 1) * policy.mutation_fraction * (high - low)
            genes.append(min(high, max(low, value)))
        lineage = tuple(dict.fromkeys((left.candidate_id, right.candidate_id)))
        return VariationDraw(tuple(genes), lineage, before, rng)
