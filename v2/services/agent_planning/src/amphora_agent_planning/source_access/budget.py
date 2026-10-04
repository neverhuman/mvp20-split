"""Per-review resource accounting; no retained payload or rights authorization."""

import math
import time
from dataclasses import dataclass, field

from ..context.policy import require


class SourceUnavailable(ValueError):
    """Transient peer observation: no guessed result or automatic retry."""


@dataclass
class ReadBudget:
    seconds: float = 20
    max_calls: int = 512
    max_bytes: int = 33554432
    deadline: float = field(init=False)
    calls: int = field(default=0, init=False)
    consumed: int = field(default=0, init=False)

    def __post_init__(self):
        require(type(self.seconds) in (int, float) and math.isfinite(self.seconds) and
                0 < self.seconds <= 30, "source_review_time_limit")
        require(type(self.max_calls) is int and 1 <= self.max_calls <= 512, "source_review_call_limit")
        require(type(self.max_bytes) is int and 1 <= self.max_bytes <= 33554432, "source_review_byte_limit")
        self.deadline = time.monotonic() + self.seconds

    def remaining(self):
        return min(self.remaining_total(), 5)

    def remaining_total(self):
        value = self.deadline - time.monotonic()
        if value <= 0:
            raise SourceUnavailable("source_review_deadline")
        return value

    def start(self):
        self.remaining()
        require(self.calls < self.max_calls, "source_review_call_limit")
        self.calls += 1

    def consume(self, size):
        self.remaining()
        self.consumed += size
        require(self.consumed <= self.max_bytes, "source_review_byte_limit")
