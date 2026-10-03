"""Focused internal outcomes; lease fields are checked against PostgreSQL authority."""

from dataclasses import dataclass
from datetime import datetime

from ..identity import EncodingWorkIdentity
from ..payloads import EncodedRepresentation
from ..validation import identifier, require


@dataclass(frozen=True, slots=True)
class LeasePolicy:
    seconds: int = 30

    def __post_init__(self):
        require(type(self.seconds) is int and 1 <= self.seconds <= 300, "representation_lease_bound")


@dataclass(frozen=True, slots=True)
class WorkLease:
    work: EncodingWorkIdentity
    actor_id: str
    token: str
    fence: int
    expires_at: datetime

    def __post_init__(self):
        require(type(self.work) is EncodingWorkIdentity, "representation_work_required")
        identifier(self.actor_id)
        identifier(self.token)
        require(type(self.fence) is int and 1 <= self.fence <= 9007199254740991, "representation_fence_bound")
        require(
            type(self.expires_at) is datetime and self.expires_at.utcoffset() is not None,
            "representation_lease_time",
        )

    def authorize(self, principal):
        require(
            self.actor_id == principal.actor_id and self.work.scope == principal.scope,
            "representation_claim_actor",
        )

    @property
    def identity(self):
        return {"actor": self.actor_id, "token": self.token, "fence": self.fence}


@dataclass(frozen=True, slots=True)
class WorkBusy:
    work: EncodingWorkIdentity
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class CacheHit:
    work: EncodingWorkIdentity
    result: EncodedRepresentation
