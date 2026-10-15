"""Immutable run retention choice, independent of current host configuration."""

from dataclasses import dataclass

from ..lifecycle.model import TransitionError
from .closures import PROFILE


KEY = "profile:artifact-retention"


@dataclass(frozen=True, slots=True)
class RetentionProfile:
    name: str | None = None

    def __post_init__(self):
        if self.name not in (None, PROFILE):
            raise TransitionError("unsupported_artifact_retention_profile")

    @classmethod
    def from_snapshot(cls, snapshot):
        if KEY not in snapshot:
            return cls()
        if snapshot[KEY] != PROFILE:
            raise TransitionError("unsupported_artifact_retention_profile")
        return cls(PROFILE)

    def pin(self, snapshot):
        if KEY in snapshot:
            raise TransitionError("artifact_retention_profile_already_pinned")
        return {**snapshot, KEY: self.name} if self.name is not None else dict(snapshot)
