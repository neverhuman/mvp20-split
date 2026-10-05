"""One bounded compiler/eligibility exchange sequence, not a persistent lease."""

import math
import time

from ..context.policy import require


class ExchangeUnavailable(ValueError):
    """No usable response; a write may already have committed."""


class ExchangeDenied(ValueError):
    """The peer denied this authenticated exchange."""


class ExchangeAbsent(ValueError):
    """An exact read was absent; this is not permission to change identity."""


class ExchangeConflict(ValueError):
    """The original command conflicts with peer-owned identity or state."""


class ExchangeInvalid(ValueError):
    """The peer explicitly rejected the request shape."""


class CompilerWindow:
    def __init__(self, owner, *, seconds=20):
        require(owner in {'runtime', 'registry'}, 'compiler_owner')
        require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= 20,
                'compiler_deadline')
        self.owner, self.deadline = owner, time.monotonic() + seconds
        self.calls = self.consumed = 0

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise ExchangeUnavailable('compiler_deadline_expired')
        return remaining

    def start(self):
        self.remaining()
        require(self.calls < (8 if self.owner == 'runtime' else 64), 'compiler_call_limit')
        self.calls += 1

    def consume(self, size):
        self.remaining()
        self.consumed += size
        if self.consumed > 16777216:
            raise ExchangeUnavailable('compiler_total_bytes')
