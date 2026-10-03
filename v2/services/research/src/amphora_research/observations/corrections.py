"""Immediate immutable observation corrections describe future selection, not live invalidation."""
from dataclasses import dataclass
from typing import ClassVar

from .identity import require
from .records import Observation


@dataclass(frozen=True, slots=True)
class ObservationCorrection:
    before: Observation
    after: Observation
    policy: ClassVar[str] = "future_campaigns_only"

    def __post_init__(self):
        require(type(self.before) is Observation and type(self.after) is Observation,"observation_correction_records_required")
        require(self.after.identity.supersedes == self.before.identity.reference,"observation_correction_predecessor_mismatch")

    @property
    def changed_fields(self):
        return tuple(name for name in ("source","binding","value","quality") if getattr(self.before,name) != getattr(self.after,name))
