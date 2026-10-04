"""Compiled owner route profiles and one review's resource accounting."""

import math
import re
import time
from dataclasses import dataclass
from types import MappingProxyType

from ..context.policy import require


class PeerUnavailable(ValueError):
    """Unknown peer state, not absence or permission to retry indefinitely."""


@dataclass(frozen=True)
class ReadProfile:
    owner: str
    seconds: int
    calls: int
    bytes: int
    routes: dict
    request_bytes: int = 4096

    def __post_init__(self):
        require(self.owner in {'knowledge', 'research'}, 'peer_read_owner')
        require(type(self.seconds) is int and 1 <= self.seconds <= 30 and
                type(self.calls) is int and 1 <= self.calls <= 160 and
                type(self.bytes) is int and 1 <= self.bytes <= 33554432 and
                type(self.request_bytes) is int and 1 <= self.request_bytes <= 262144, 'peer_read_limits')
        require(type(self.routes) is dict and 1 <= len(self.routes) <= 8, 'peer_read_routes')
        for path, (_, _, limit) in self.routes.items():
            named_view = self.owner == 'research' and path in {
                '/v1/research-explore/catalog', '/v1/research-explore/specimens',
                '/v1/research-explore/properties', '/v1/research-explore/observation-series'}
            require(type(path) is str and (re.fullmatch(r'/v1/[a-z-]+/read', path) is not None or named_view) and
                    type(limit) is int and 1 <= limit <= 16777216, 'peer_read_route')
        object.__setattr__(self, 'routes', MappingProxyType(dict(self.routes)))

    def code(self, reason):
        return self.owner + '_' + reason


class ReadWindow:
    def __init__(self, profile, seconds):
        require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= profile.seconds,
                profile.code('read_deadline'))
        self.profile, self.seconds = profile, seconds
        self.deadline, self.calls, self.consumed = time.monotonic() + seconds, 0, 0

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise PeerUnavailable(self.profile.code('read_expired'))
        return remaining

    def start(self):
        self.remaining()
        require(self.calls < self.profile.calls, self.profile.code('read_call_limit'))
        self.calls += 1

    def consume(self, size):
        self.remaining()
        self.consumed += size
        require(self.consumed <= self.profile.bytes, self.profile.code('read_byte_limit'))
