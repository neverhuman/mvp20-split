"""Conservative local lease observations; runtime alone grants and fences authority."""

import math
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from amphora_contracts_runtime import AttemptRef

from .transport import ProtocolError


class Clock:
    def monotonic(self):
        return time.monotonic()

    def utc(self):
        return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class RenewalResult:
    attempt: AttemptRef
    run_revision: int
    expires_at: datetime
    deadline: datetime


class ToolAttemptContext:
    """Stage-bound renewal for bounded pure kernels; no new attempt/work authority."""

    def __init__(self, runtime, claimed, lease_seconds=30, clock=None, skew_seconds=1.0):
        if (type(lease_seconds) is not int or not 10 <= lease_seconds <= 300
            or isinstance(skew_seconds, bool) or not isinstance(skew_seconds, (int, float))
            or not math.isfinite(skew_seconds) or not 0 <= skew_seconds <= 5):
            raise ProtocolError("invalid_lease_profile")
        self.runtime = runtime
        self.invocation = claimed.invocation
        self.attempt = AttemptRef(run_id=self.invocation.run_id, invocation_id=self.invocation.invocation_id,
            attempt_id=self.invocation.attempt_id, fence=self.invocation.fence)
        self.lease_seconds = lease_seconds
        self.clock = clock or Clock()
        self.skew_seconds = skew_seconds
        self._stopped = False
        self._until = self.clock.monotonic() + min(lease_seconds,
            (datetime.fromisoformat(claimed.lease_expires_at) - self.clock.utc()).total_seconds()) - skew_seconds

    def check(self):
        if self._stopped or self.clock.monotonic() >= self._until:
            self._stopped = True
            raise ProtocolError("attempt_authority_lost")

    def refresh(self):
        self.check()
        started = self.clock.monotonic()
        try:
            receipt = self.runtime.renew(self.attempt, "renew-" + uuid.uuid4().hex,
                lease_seconds=self.lease_seconds, guard=self.check)
            snapshot = self.runtime.run(self.attempt.run_id)
            activation = next((a for a in snapshot.activations if a.invocation_id == self.attempt.invocation_id), None)
            attempt = None if activation is None else activation.latest_attempt
            if (snapshot.status != "running" or snapshot.revision < receipt.outcome.committed.revision
                or activation is None or activation.status != "leased" or activation.fence != self.attempt.fence
                or attempt is None or attempt.attempt_id != self.attempt.attempt_id or attempt.fence != self.attempt.fence
                or attempt.worker_id != self.runtime.identity.actor_id or attempt.status != "leased"):
                raise ProtocolError("attempt_authority_lost")
            result = RenewalResult(self.attempt, snapshot.revision, datetime.fromisoformat(attempt.lease_expires_at),
                                   datetime.fromisoformat(attempt.deadline))
            remaining = (min(result.expires_at, result.deadline) - self.clock.utc()).total_seconds()
            self._until = min(started + self.lease_seconds, self.clock.monotonic() + remaining) - self.skew_seconds
            self.check()
            return result
        except (ProtocolError, ValueError):
            self._stopped = True
            raise
