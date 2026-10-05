"""Explicit current-use failures and relevant changes; no latest-head or lease claim."""

from dataclasses import dataclass
from datetime import datetime

from ..campaign_proposals.observations import ObservationKey
from .plan import RefreshPlan


@dataclass(frozen=True)
class RefreshFinding:
    owner: str
    identity: bytes
    code: str


@dataclass(frozen=True)
class RefreshChange:
    key: ObservationKey
    before_sha256: str | None
    after_sha256: str | None


@dataclass(frozen=True)
class RefreshResult:
    plan: RefreshPlan
    observed_at: datetime
    processing_artifacts: tuple
    changes: tuple[RefreshChange, ...]
    failures: tuple[RefreshFinding, ...]
    scientific_gaps: tuple[RefreshFinding, ...]

    @property
    def ready_for_preparation(self):
        return not self.failures and not self.changes

    @property
    def latest_research_head_verified(self):
        return False
