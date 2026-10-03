"""Retained exact projection evidence, pinned to one immutable build attempt."""

from dataclasses import dataclass

from .identity import BuildAttempt
from .validation import digest, require


@dataclass(frozen=True, slots=True)
class VerifiedProjection:
    attempt: BuildAttempt
    manifest_sha256: str
    projection_sha256: str
    point_count: int

    def __post_init__(self):
        require(type(self.attempt) is BuildAttempt, "retrieval_attempt_required")
        digest(self.manifest_sha256)
        digest(self.projection_sha256)
        require(
            type(self.point_count) is int and 1 <= self.point_count <= 256, "retrieval_verification_bound"
        )

    def descriptor(self):
        return {
            "format": "data.index-verification.v1",
            "generation": self.attempt.generation.descriptor(),
            "token": self.attempt.token,
            "fence": self.attempt.fence,
            "namespace": self.attempt.namespace,
            "manifest_sha256": self.manifest_sha256,
            "projection_sha256": self.projection_sha256,
            "point_count": self.point_count,
        }
