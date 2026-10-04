"""One metadata operation's closed resource accounting, separate from source rights."""

import math
import time

from ..context.policy import require


class MetadataWindow:
    def __init__(self, owner, seconds=30):
        require(owner in {"registry", "runtime", "data"}, "metadata_owner")
        require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= 30, "metadata_seconds")
        self.owner, self.deadline = owner, time.monotonic() + seconds
        self.max_calls = {"registry": 8, "runtime": 257, "data": 32}[owner]
        self.calls, self.consumed = 0, 0

    def remaining(self):
        result = self.deadline - time.monotonic()
        require(result > 0, "metadata_deadline")
        return result

    def start(self):
        self.remaining()
        require(self.calls < self.max_calls, "metadata_call_limit")
        self.calls += 1

    def consume(self, count):
        self.remaining()
        self.consumed += count
        require(self.consumed <= 16777216, "metadata_byte_limit")
