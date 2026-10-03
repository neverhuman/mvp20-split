"""Permitted phase edges only; verified/published transitions still require owner evidence."""

from enum import Enum

from .validation import require


class GenerationPhase(str, Enum):
    PREPARED = "prepared"
    BUILDING = "building"
    VERIFIED = "verified"
    PUBLISHED = "published"
    FAILED = "failed"
    ABANDONED = "abandoned"

    def require_successor(self, target):
        require(type(target) is GenerationPhase, "retrieval_phase_required")
        edges = {
            self.PREPARED: (self.BUILDING, self.ABANDONED),
            self.BUILDING: (self.VERIFIED, self.FAILED, self.ABANDONED),
            self.VERIFIED: (self.PUBLISHED, self.FAILED, self.ABANDONED),
        }
        require(target in edges.get(self, ()), "retrieval_phase_transition")
        return target
