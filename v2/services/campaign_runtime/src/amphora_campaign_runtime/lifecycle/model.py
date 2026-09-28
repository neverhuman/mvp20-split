"""Immutable authority, budget and lease rules; database time is supplied by the owner."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta

SAFE_MAX = 9007199254740991


class TransitionError(ValueError):
    """Stable reason code; not a wire receipt or scientific judgment."""


def integer(value, minimum=0, maximum=SAFE_MAX):
    if type(value) is not int or not minimum <= value <= maximum:
        raise TransitionError("invalid_counter")


def timestamp(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise TransitionError("timezone_required")


@dataclass(frozen=True, slots=True)
class RunBudget:
    limit: int
    reserved: int = 0
    spent: int = 0

    def __post_init__(self):
        integer(self.limit, 1)
        integer(self.reserved)
        integer(self.spent)
        if self.reserved + self.spent > self.limit:
            raise TransitionError("budget_invariant")

    @property
    def available(self):
        return self.limit - self.reserved - self.spent

    def issue(self):
        if not self.available:
            raise TransitionError("budget_exhausted")
        return replace(self, reserved=self.reserved + 1)

    def settle(self):
        if not self.reserved:
            raise TransitionError("no_reserved_unit")
        return replace(self, reserved=self.reserved - 1, spent=self.spent + 1)


@dataclass(frozen=True, slots=True)
class WorkerAuthority:
    worker_id: str
    revoked: bool = False
    revision: int = 0

    def __post_init__(self):
        integer(self.revision)
        if not self.worker_id or type(self.revoked) is not bool:
            raise TransitionError("invalid_worker_policy")

    def require(self, worker_id):
        if worker_id != self.worker_id:
            raise TransitionError("worker_mismatch")
        if self.revoked:
            raise TransitionError("worker_revoked")

    def revoke(self):
        return self if self.revoked else replace(self, revoked=True, revision=self.revision + 1)


@dataclass(frozen=True, slots=True)
class RunState:
    status: str = "running"
    revision: int = 0

    def __post_init__(self):
        integer(self.revision)
        if self.status not in {"running", "completed", "cancelled", "failed", "blocked"}:
            raise TransitionError("invalid_run_status")

    def require_running(self):
        if self.status != "running":
            raise TransitionError("run_not_running")

    def cancel(self, expected_revision=None):
        if expected_revision is not None and expected_revision != self.revision:
            raise TransitionError("run_revision_conflict")
        if self.status == "cancelled":
            return self
        self.require_running()
        return replace(self, status="cancelled", revision=self.revision + 1)


@dataclass(frozen=True, slots=True)
class AttemptLease:
    attempt_id: str
    worker_id: str
    fence: int
    expires_at: datetime
    deadline: datetime
    status: str = "leased"
    settled: bool = False

    def __post_init__(self):
        integer(self.fence, 1)
        timestamp(self.expires_at)
        timestamp(self.deadline)
        if not self.attempt_id or not self.worker_id or self.expires_at > self.deadline:
            raise TransitionError("invalid_lease")
        if self.status not in {"leased", "succeeded", "abstained", "failed", "expired", "cancelled", "uncertain"}:
            raise TransitionError("invalid_attempt_status")
        if type(self.settled) is not bool or self.settled != (self.status not in {"leased", "uncertain"}):
            raise TransitionError("invalid_settlement")

    @classmethod
    def issue(cls, attempt_id, worker_id, fence, now, deadline, seconds):
        integer(seconds, 1, 300)
        timestamp(now)
        timestamp(deadline)
        if now >= deadline:
            raise TransitionError("invocation_deadline")
        return cls(attempt_id, worker_id, fence, min(now + timedelta(seconds=seconds), deadline), deadline)

    def authorize(self, run, authority, *, worker_id, attempt_id, current_fence, now):
        timestamp(now)
        run.require_running()
        if authority is None:
            raise TransitionError("worker_unauthorized")
        authority.require(worker_id)
        if (worker_id != self.worker_id or attempt_id != self.attempt_id or current_fence != self.fence):
            raise TransitionError("stale_attempt")
        if self.status != "leased":
            raise TransitionError("attempt_not_leased")
        if now >= self.expires_at or now >= self.deadline:
            raise TransitionError("lease_expired")

    def renew(self, run, authority, *, worker_id, attempt_id, current_fence, now, seconds):
        self.authorize(run, authority, worker_id=worker_id, attempt_id=attempt_id, current_fence=current_fence, now=now)
        integer(seconds, 1, 300)
        return replace(self, expires_at=min(self.deadline, max(self.expires_at, now + timedelta(seconds=seconds))))

    def finish(self, budget, status, *, resolved=False):
        if status not in {"succeeded", "abstained", "failed", "expired", "cancelled", "uncertain"}:
            raise TransitionError("invalid_terminal_status")
        if self.status == "uncertain" and status != "uncertain" and not resolved:
            raise TransitionError("uncertainty_unresolved")
        if self.status not in {"leased", "uncertain"}:
            if self.status != status:
                raise TransitionError("terminal_attempt_conflict")
            return self, budget  # Duplicate settlement spends no second unit.
        if status == "uncertain":
            return replace(self, status=status), budget  # Retain reservation until authoritative reconciliation.
        return replace(self, status=status, settled=True), budget.settle()


@dataclass(frozen=True, slots=True)
class ActivationState:
    status: str = "queued"
    fence: int = 0
    issued: int = 0
    max_attempts: int = 3
    effect: str = "pure"

    def __post_init__(self):
        integer(self.fence)
        integer(self.issued, 0, 100)
        integer(self.max_attempts, 1, 100)
        if self.issued > self.max_attempts or self.fence < self.issued:
            raise TransitionError("activation_counter_invariant")
        if self.status not in {"queued", "leased", "succeeded", "abstained", "failed", "cancelled", "uncertain"}:
            raise TransitionError("invalid_activation_status")
        if self.effect not in {"pure", "external"}:
            raise TransitionError("invalid_effect_policy")

    def claim(self, run, authority, budget, *, worker_id, attempt_id, now, deadline, seconds=30):
        run.require_running()
        if authority is None:
            raise TransitionError("worker_unauthorized")
        authority.require(worker_id)
        if self.effect != "pure":
            raise TransitionError("effectful_fixture_forbidden")
        if self.status != "queued":
            raise TransitionError("activation_not_queued")
        if self.issued >= self.max_attempts:
            raise TransitionError("attempt_limit")
        lease = AttemptLease.issue(attempt_id, worker_id, self.fence + 1, now, deadline, seconds)
        return replace(self, status="leased", fence=lease.fence, issued=self.issued + 1), lease, budget.issue()

    def terminal(self, lease, budget, disposition, *, now, run, retryable=False, authority=None):
        timestamp(now)
        if lease.fence == self.fence and lease.settled and lease.status == disposition and self.status not in {"leased", "uncertain"}:
            return self, lease, budget
        if lease.fence != self.fence or self.status not in {"leased", "uncertain"}:
            raise TransitionError("stale_attempt")
        if disposition == "expired" and now < lease.expires_at:
            raise TransitionError("lease_not_expired")
        if disposition in {"succeeded", "abstained"}:
            lease.authorize(run, authority, worker_id=lease.worker_id, attempt_id=lease.attempt_id,
                            current_fence=self.fence, now=now)
        if self.effect != "pure" and disposition == "expired":
            disposition = "uncertain"
        lease, budget = lease.finish(budget, disposition)
        status = disposition
        can_retry = (self.effect == "pure" and run.status == "running" and self.issued < self.max_attempts
                     and budget.available > 0 and now < lease.deadline)
        if disposition == "expired" or (disposition == "failed" and retryable):
            status = "queued" if can_retry else "failed"
        if disposition == "uncertain":
            status = "uncertain"
        return replace(self, status=status), lease, budget

    def cancel_unclaimed(self):
        if self.status != "queued":
            raise TransitionError("activation_not_queued")
        return replace(self, status="cancelled")
