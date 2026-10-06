"""Committed decisions gate ready work; a recorded response alone never releases it."""

from dataclasses import dataclass

from ..supervision_checkpoints.storage import CheckpointStore
from .storage import WinnerStore


@dataclass(frozen=True)
class CheckpointGate:
    released: bool
    changed: bool = False
    block_reason: str | None = None

    @classmethod
    def read(cls, conn, params, path):
        opened = CheckpointStore.ensure(conn, params, path)
        slot = opened.checkpoint
        winner = WinnerStore.load(conn, {**params, 'decision': slot.seed.decision_id}, slot)
        if winner is None:
            return cls(False, opened.created)
        outcome = winner.document().outcome
        if outcome.kind == 'cancelled' or (outcome.kind == 'fallback' and outcome.action == 'block_target'):
            return cls(False, True, outcome.reason_code)
        # B2.02d connects the same selected fields at conversion opening and revalidation.
        # Until then never issue original scalar values after accepting a different selection.
        if winner.selection is not None:
            return cls(False)
        return cls(True)
