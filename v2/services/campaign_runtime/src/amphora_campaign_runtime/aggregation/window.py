"""Declared deadline eligibility; the caller supplies locked database time."""

from dataclasses import dataclass
from datetime import timedelta

from ..lifecycle.model import timestamp
from .snapshot import require


@dataclass(frozen=True)
class CollectionWindow:
    opened_at: object
    run_deadline: object

    def expired(self, policy, now):
        if policy.kind != "partial" or policy.close != "deadline":
            return False
        require(self.opened_at is not None, "aggregate_clock_unavailable")
        timestamp(self.opened_at)
        timestamp(self.run_deadline)
        timestamp(now)
        require(self.opened_at < self.run_deadline, "aggregate_clock_invalid")
        require(policy.deadline_seconds is not None, "aggregate_deadline_policy")
        return now >= min(self.opened_at + timedelta(seconds=policy.deadline_seconds), self.run_deadline)
