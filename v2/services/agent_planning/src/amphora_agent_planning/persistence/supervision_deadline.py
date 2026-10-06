"""Resolve the immutable checkpoint deadline inside the request transaction."""

from datetime import datetime, timedelta, timezone

from ..supervision_intake.snapshot import CheckpointIntakeSnapshot
from ..supervision_intake.storage import SupervisionIntake


def checkpoint_deadline(connection, key, principal):
    snapshot = SupervisionIntake._wrapper(connection, key, principal)
    if not isinstance(snapshot, CheckpointIntakeSnapshot):
        return None
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(
        milliseconds=snapshot.document().deadline_unix_ms)
