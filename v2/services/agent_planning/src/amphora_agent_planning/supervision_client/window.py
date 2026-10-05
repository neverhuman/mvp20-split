"""One explicit bounded peer sequence; no retained state or retry policy."""

import math
import time

from ..context.policy import require


class ExchangeUnavailable(ValueError):
    """A write may have committed; recover its original receipt before deciding next steps."""


class ExchangeDenied(ValueError):
    pass


class ExchangeAbsent(ValueError):
    pass


class ExchangeConflict(ValueError):
    pass


class ExchangeInvalid(ValueError):
    pass


class ExchangeWindow:
    def __init__(self, seconds=10):
        require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= 10, 'supervisor_deadline')
        self.deadline = time.monotonic() + seconds
        self.calls = self.consumed = 0

    def remaining(self):
        value = self.deadline - time.monotonic()
        if value <= 0:
            raise ExchangeUnavailable('supervisor_deadline_expired')
        return value

    def start(self):
        self.remaining()
        require(self.calls < 3, 'supervisor_call_limit')
        self.calls += 1

    def consume(self, size):
        self.remaining()
        self.consumed += size
        if self.consumed > 524288:
            raise ExchangeUnavailable('supervisor_total_bytes')
