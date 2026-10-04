"""Relevant metadata comparison, not latest-head selection or active invalidation."""

import hashlib
from dataclasses import dataclass

from ..context.policy import require
from .records import ResearchIdentity, canonical


@dataclass(frozen=True)
class ResearchRead:
    identity: ResearchIdentity
    observation_sha256: str

    @classmethod
    def available(cls, record):
        return cls(record.identity, hashlib.sha256(canonical({"record_sha256": record.sha256})).hexdigest())

    @classmethod
    def unavailable(cls, gap):
        return cls(gap.identity, hashlib.sha256(canonical({"unavailable": gap.reason})).hexdigest())


@dataclass(frozen=True)
class ReadChange:
    identity: ResearchIdentity
    reason: str


@dataclass(frozen=True)
class ResearchReadSet:
    entries: tuple[ResearchRead, ...]

    def __post_init__(self):
        require(type(self.entries) is tuple and len(self.entries) <= 160, "campaign_read_set_limit")
        require(len({item.identity for item in self.entries}) == len(self.entries), "campaign_read_set_duplicate")

    def changes(self, observed):
        current = {item.identity: item.observation_sha256 for item in observed.entries}
        return tuple(ReadChange(item.identity, "missing" if item.identity not in current else "changed")
                     for item in self.entries if current.get(item.identity) != item.observation_sha256)
