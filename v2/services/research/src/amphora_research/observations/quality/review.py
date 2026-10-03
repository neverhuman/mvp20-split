"""A qualified point retains original evidence and separate match, use and focus dimensions."""
from dataclasses import dataclass

from ..matching import ObservationMatch
from ..normalization.transform import NormalizedMeasurement
from ..records import Observation


@dataclass(frozen=True, slots=True)
class ObservationUseReview:
    observation: Observation
    raw_match: ObservationMatch
    match: ObservationMatch
    normalization: NormalizedMeasurement | None
    blockers: tuple[str, ...]
    gaps: tuple[str, ...]
    focus: tuple[str, ...]

    @property
    def disposition(self):
        if self.match.reasons:
            return "quarantined"
        if self.blockers:
            return "excluded"
        return "unresolved" if self.gaps else "usable"
