"""Versioned synthetic encoding equivalence; no cache-access authority."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_candidate_spaces import NumericDesign

from .domain import NumericSpace
from .profile import canonical, pin

EQUIVALENCE = pin(
    "synthetic-numeric-equivalence",
    "ordered coordinates and exact JSON numeric values, units and bounds; all source fields including scope and unknowns preserved",
)


@dataclass(frozen=True)
class NumericCanonical:
    record: NumericDesign

    def __post_init__(self):
        object.__setattr__(self, "record", NumericSpace(self.record).record)

    @property
    def bytes(self):
        return canonical(self.record)

    @property
    def sha256(self):
        return hashlib.sha256(self.bytes).hexdigest()

    @property
    def policy(self):
        return EQUIVALENCE
