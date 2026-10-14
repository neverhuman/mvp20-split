"""Numeric birth invariants reuse the existing box and counter-RNG mathematics."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_population import CandidateBirth
from amphora_contracts_search import RngInterval

from ..randomness import CounterRandom
from ..ranking import require
from ..specification import NumericBox
from ..variation import BoxVariation
from .specification import OriginalPopulation, canonical


def birth_digest(original, record):
    parts = ["numeric-population-birth-v1", original.digest, record.generation, record.ordinal,
             record.operator, [value.hex() for value in record.genes], list(record.parents),
             record.draws.start, record.draws.end]
    return hashlib.sha256(json.dumps(parts, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class NumericBirth:
    original: OriginalPopulation
    record: CandidateBirth

    def __post_init__(self):
        record = CandidateBirth.model_validate_json(self.record.model_dump_json())
        object.__setattr__(self, "record", record)
        require(len(canonical(record)) <= 8192, "birth_bytes")
        require(record.scope == self.original.record.scope and record.specification_sha256 == self.original.digest,
                "birth_original")
        require(record.candidate_id == birth_digest(self.original, record), "birth_identity")
        require(record.generation <= self.original.record.budget.successor_generations
                and record.ordinal < self.original.record.budget.population_size, "birth_position")
        box = NumericBox(tuple((v.lower, v.upper) for v in self.original.record.variables))
        require(box.contains(record.genes), "birth_bounds")
        require(len(record.parents) == len(set(record.parents)) and record.candidate_id not in record.parents, "birth_parents")
        if record.operator == "seed":
            require(record.generation == 0 and not record.parents, "birth_seed_ancestry")
            require(record.draws.start == record.ordinal * len(record.genes)
                    and record.draws.end == record.draws.start + len(record.genes), "birth_seed_draws")
            expected, _ = box.sample(CounterRandom(self.original.record.seed, record.draws.start))
            require(record.genes == expected, "birth_seed_replay")
        else:
            require(record.generation > 0 and bool(record.parents), "birth_variation_ancestry")
            require(record.draws.end - record.draws.start == 3 + 3 * len(record.genes), "birth_variation_draws")
        if record.disposition == "proposed":
            require(record.reason_code is None and record.duplicate_of is None, "birth_proposed")
        elif record.disposition == "duplicate":
            require(record.reason_code == "duplicate_genes" and record.duplicate_of is not None
                    and record.duplicate_of != record.candidate_id, "birth_duplicate")
        else:
            require(record.reason_code is not None and record.duplicate_of is None, "birth_rejected")

    @classmethod
    def seed(cls, original, ordinal):
        require(type(ordinal) is int and 0 <= ordinal < original.record.budget.population_size, "birth_position")
        box = NumericBox(tuple((v.lower, v.upper) for v in original.record.variables))
        start = ordinal * len(box.bounds)
        genes, after = box.sample(CounterRandom(original.record.seed, start))
        record = CandidateBirth(schema_version="1", profile="numeric-population-birth-v1", scope=original.record.scope,
            specification_sha256=original.digest, candidate_id="0" * 64, generation=0, ordinal=ordinal,
            operator="seed", genes=genes, parents=(), draws=RngInterval(start=start, end=after.counter),
            disposition="proposed", reason_code=None, duplicate_of=None)
        return cls(original, record.model_copy(update={"candidate_id": birth_digest(original, record)}))

    @classmethod
    def vary(cls, original, generation, ordinal, parents, rng):
        # Reuse the unchanged numerical kernel, with the new profile's explicit bounds.
        draw = BoxVariation(original).draw(parents, rng)
        record = CandidateBirth(schema_version="1", profile="numeric-population-birth-v1", scope=original.record.scope,
            specification_sha256=original.digest, candidate_id="0" * 64, generation=generation, ordinal=ordinal,
            operator="variation", genes=draw.genes, parents=draw.parents,
            draws=RngInterval(start=draw.before.counter, end=draw.after.counter),
            disposition="proposed", reason_code=None, duplicate_of=None)
        return cls(original, record.model_copy(update={"candidate_id": birth_digest(original, record)}))

    def verify_parent_pool(self, parents):
        require(self.record.operator == "variation", "birth_not_variation")
        expected = self.vary(self.original, self.record.generation, self.record.ordinal, parents,
                             CounterRandom(self.original.record.seed, self.record.draws.start))
        require(expected.record.candidate_id == self.record.candidate_id, "birth_variation_replay")
