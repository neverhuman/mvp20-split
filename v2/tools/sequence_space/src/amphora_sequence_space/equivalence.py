"""Versioned synthetic encoding equivalence; no cache-access authority."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_candidate_spaces import SequenceDesign

from .domain import SequenceSpace
from .profile import canonical, pin

EQUIVALENCE = pin(
    "synthetic-sequence-equivalence",
    "exact uppercase DNA order and all source fields including scope preserved",
)


@dataclass(frozen=True)
class SequenceCanonical:
    record: SequenceDesign

    def __post_init__(self):
        object.__setattr__(self, "record", SequenceSpace(self.record).record)

    @property
    def bytes(self):
        return canonical(self.record)

    @property
    def sha256(self):
        return hashlib.sha256(self.bytes).hexdigest()

    @property
    def policy(self):
        return EQUIVALENCE
