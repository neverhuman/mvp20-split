"""Original search binding and finite box behavior; records are only transport."""

import json
import math
from dataclasses import dataclass
from hashlib import sha256

from amphora_contracts_search import SearchSpec

from .randomness import CounterRandom
from .ranking import ObjectiveSpace, require


def canonical_bytes(record) -> bytes:
    """search-json-v1: validated DTO JSON, sorted keys, UTF-8, no trailing LF."""
    return json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class NumericBox:
    bounds: tuple[tuple[float, float], ...]

    def __post_init__(self):
        require(type(self.bounds) is tuple and 1 <= len(self.bounds) <= 32, "box_dimensions")
        for pair in self.bounds:
            require(type(pair) is tuple and len(pair) == 2, "box_pair")
            require(all(type(x) is float and math.isfinite(x) and abs(x) <= 1e100 for x in pair), "box_finite")
            require(pair[0] <= pair[1], "box_order")

    def contains(self, genes) -> bool:
        return (type(genes) is tuple and len(genes) == len(self.bounds)
                and all(type(x) is float and math.isfinite(x) and low <= x <= high
                        for x, (low, high) in zip(genes, self.bounds, strict=True)))

    def sample(self, rng: CounterRandom) -> tuple[tuple[float, ...], CounterRandom]:
        genes = []
        for low, high in self.bounds:
            draw, rng = rng.draw()  # Fixed axes consume a draw too: topology-independent accounting.
            value = low + (high - low) * draw
            genes.append(min(high, max(low, value)))
        return tuple(genes), rng


@dataclass(frozen=True)
class OriginalSearch:
    record: SearchSpec

    def __post_init__(self):
        checked = SearchSpec.model_validate_json(self.record.model_dump_json())
        object.__setattr__(self, "record", checked)
        _ = self.box  # Validate ordered variable ranges before producing any state.
        for label, ids in (
            ("variable", [v.variable_id for v in checked.variables]),
            ("objective", [o.objective_id for o in checked.objectives]),
            ("implementation", [p.name for p in checked.implementations]),
        ):
            require(len(ids) == len(set(ids)), f"duplicate_{label}")
        require(all(v.unit.strip() for v in (*checked.variables, *checked.objectives)), "blank_unit")
        references = (checked.evaluator.constraints, *checked.evaluator.context)
        require(all(ref.scope == checked.scope for ref in references), "specification_scope")
        identities = [ref.artifact_id for ref in references]
        require(len(set(identities)) == len(identities), "duplicate_context")

    @property
    def digest(self) -> str:
        return sha256(canonical_bytes(self.record)).hexdigest()

    @property
    def box(self) -> NumericBox:
        return NumericBox(tuple((v.lower, v.upper) for v in self.record.variables))

    @property
    def objectives(self) -> ObjectiveSpace:
        return ObjectiveSpace(tuple(o.direction for o in self.record.objectives))

    def initial_random(self) -> CounterRandom:
        return CounterRandom(self.record.seed)

    def require_binding(self, specification: SearchSpec, digest: str) -> None:
        received = OriginalSearch(specification)
        require(digest == self.digest == received.digest, "original_specification")

    def resume_random(self, state) -> CounterRandom:
        return CounterRandom.from_record(state, expected_seed=self.record.seed)
