"""Portable immutable SHA-256 counter stream, independent of Python random."""

import re
from dataclasses import dataclass
from hashlib import sha256

from amphora_contracts_search import RngState

from .ranking import require

MAX_COUNTER = (1 << 53) - 1
NAMESPACE = b"amphora.search/sha256-counter-u53-v1\x00"


@dataclass(frozen=True)
class CounterRandom:
    seed: str
    counter: int = 0

    def __post_init__(self):
        require(type(self.seed) is str and re.fullmatch(r"[0-9a-f]{64}", self.seed), "rng_seed")
        require(type(self.counter) is int and 0 <= self.counter <= MAX_COUNTER, "rng_counter")

    def draw(self) -> tuple[float, "CounterRandom"]:
        require(self.counter < MAX_COUNTER, "rng_exhausted")
        payload = NAMESPACE + bytes.fromhex(self.seed) + self.counter.to_bytes(8, "big")
        numerator = int.from_bytes(sha256(payload).digest()[:8], "big") >> 11
        return numerator / (1 << 53), CounterRandom(self.seed, self.counter + 1)

    def to_record(self) -> RngState:
        return RngState(algorithm="sha256-counter-u53-v1", seed=self.seed, counter=self.counter)

    @classmethod
    def from_record(cls, state: RngState, *, expected_seed: str) -> "CounterRandom":
        # JSON validation also rejects deliberately constructed/unvalidated DTOs.
        checked = RngState.model_validate_json(state.model_dump_json())
        require(checked.seed == expected_seed, "rng_original_seed")
        return cls(checked.seed, checked.counter)
