"""Bounded upload recovery; never delete bytes or infer completion from a dead worker."""

import json
from dataclasses import dataclass

from amphora_contracts_artifacts import ContentDescriptor
from sqlalchemy import text

from .model import UploadAttempt, UploadError
from .uploads import SCOPE, Uploads


@dataclass(frozen=True, slots=True)
class UploadRecovery:
    status: str
    generation: int
    selected: dict | None
    live_stream: bool
    expired_stream: bool

    def terminal_reason(self, limits):
        if self.status == "abandoned":
            return "upload_abandoned"
        if (
            self.selected is None
            and not self.live_stream
            and not self.expired_stream
            and self.generation >= limits.attempts
        ):
            return "attempt_limit"
        return None


class StreamRecovery:
    def __init__(self, uploads, storage):
        self.uploads, self.storage = uploads, storage

    @staticmethod
    def inspect_in(connection, principal, upload_id):
        principal.require("upload")
        key = principal.bindings | {"upload": upload_id}
        row = (
            connection.execute(
                text(
                    "SELECT status,generation FROM artifacts.uploads WHERE "
                    + SCOPE
                    + " AND actor_id=:actor AND upload_id=:upload"
                ),
                key,
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise UploadError("upload_unavailable")
        streams = (
            connection.execute(
                text(
                    "SELECT "
                    "coalesce(bool_or(expires_at>clock_timestamp()),false) AS live,"
                    "coalesce(bool_or(expires_at<=clock_timestamp()),false) AS expired "
                    "FROM artifacts.upload_attempts WHERE "
                    + SCOPE
                    + " AND upload_id=:upload AND status='streaming'"
                ),
                key,
            )
            .mappings()
            .one()
        )
        return UploadRecovery(
            row["status"],
            row["generation"],
            Uploads.selected_in(connection, principal, upload_id),
            streams["live"],
            streams["expired"],
        )

    def inspect(self, principal, upload_id):
        with self.uploads.commands.engine.connect() as connection:
            return self.inspect_in(connection, principal, upload_id)

    def settle_expired(self, principal, upload_id):
        principal.require("upload")
        with self.uploads.commands.engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        "SELECT a.*,u.expected_descriptor FROM artifacts.upload_attempts a "
                        "JOIN artifacts.uploads u USING(tenant_id,project_id,upload_id) "
                        "WHERE u.tenant_id=:tenant AND u.project_id=:project AND u.actor_id=:actor AND u.upload_id=:upload "
                        "AND a.status='streaming' AND a.expires_at<=clock_timestamp() ORDER BY a.generation LIMIT 1"
                    ),
                    principal.bindings | {"upload": upload_id},
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            return False
        attempt = UploadAttempt(
            upload_id,
            row["attempt_id"],
            row["generation"],
            row["storage_key"],
            ContentDescriptor.model_validate_json(json.dumps(row["expected_descriptor"])),
        )
        try:
            with self.storage.guard(attempt.storage_key):
                # A closed writer is proven by its OS lock. Prevent a delayed writer before freeing its stream slot.
                # Retain all allocation and bytes; only existing explicit cleanup may delete/refund them.
                self.storage.fence_writer(attempt.storage_key)
                self.uploads.finish(principal, attempt, verified=False, actual_bytes=None)
            return True
        except OSError:
            return False
