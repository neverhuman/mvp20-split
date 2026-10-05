"""Owned immutable command histories and bounded check-round projections."""

from dataclasses import dataclass
from datetime import datetime

from ..campaign_authoring import AuthoringRequest
from ..campaign_eligibility.request import EligibilityRequest
from .effect import CompilerEffect
from .events import CompilerEvent, CompilerProgress


@dataclass(frozen=True)
class StoredCompilerEvent:
    event: CompilerEvent
    recorded_at: datetime


@dataclass(frozen=True)
class CompilerOperation:
    effect: CompilerEffect
    request: AuthoringRequest | EligibilityRequest
    progress: CompilerProgress
    registered_at: datetime
    events: tuple[StoredCompilerEvent, ...]

    @property
    def terminal(self):
        return self.progress.terminal


@dataclass(frozen=True)
class CompilerRound:
    check_id: str
    ordinal: int
    registered_at: datetime
    operations: tuple[CompilerOperation, ...]

    @property
    def terminal(self):
        return bool(self.operations) and all(item.terminal for item in self.operations)

    @property
    def next_operation(self):
        return next((item for item in self.operations if not item.terminal), None)
