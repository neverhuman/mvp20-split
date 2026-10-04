"""Lease-fenced preparation and append-only publication transitions."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from ..context.policy import require
from .attempt import PublicationAttempt
from .identity import PublicationIdentity
from .payload import TraceArtifact
from .records import PayloadRecord, PublicationEvent, advance
from .review_record import ReviewRecord
from .store import KEY, LEASE, PublicationStore


@dataclass(frozen=True)
class PublicationState:
    identity: PublicationIdentity
    payload: PayloadRecord | None
    attempt: PublicationAttempt | None
    position: int
    prepared_at: datetime | None
    events: tuple[tuple[PublicationEvent, datetime], ...]


class PublicationJournal:
    def __init__(self, store: PublicationStore):
        self.store = store

    def _facts(self, connection, principal, identity):
        stored = self.store.extractions._trace(connection, principal, identity.trace())
        require(stored is not None, "publication_trace_unknown")
        task = self.store.extractions._task(connection, principal, stored.projection.document().task_id)
        require(task is not None, "extraction_task_unknown")
        return stored.projection, task.snapshot

    def _read(self, connection, principal, key):
        identity = self.store.identity(connection, principal, key)
        if identity is None:
            return None
        position = connection.execute(text("SELECT position FROM planning.trace_publication_control WHERE " + KEY),
                                       key).scalar_one()
        row = connection.execute(text("SELECT * FROM planning.trace_publication_payloads WHERE " + KEY),
                                 key).mappings().first()
        if row is None:
            require(position == 0, "stored_publication_position")
            return PublicationState(identity, None, None, 0, None, ())
        projection, task = self._facts(connection, principal, identity)
        payload = PayloadRecord.from_row(row, identity, projection, task, self.store.schema)
        rows = connection.execute(text("SELECT * FROM planning.trace_publication_events WHERE " + KEY +
                                       " ORDER BY position LIMIT 65"), key).mappings().all()
        require(0 < len(rows) == position <= 64, "stored_publication_position")
        attempt, events = None, []
        for index, entry in enumerate(rows, 1):
            event = PublicationEvent(bytes(entry["canonical_bytes"]))
            require(entry["position"] == index and entry["event_sha256"] == event.sha256,
                    "stored_publication_event_digest")
            attempt = event.apply(attempt, identity, payload.artifact, index)
            events.append((event, entry["recorded_at"]))
        return PublicationState(identity, payload, attempt, position, row["prepared_at"], tuple(events))

    def read(self, principal, publication_id):
        principal.require("read_attempts", principal.scope)
        key = self.store.key(principal, publication_id)
        with self.store.engine.begin() as connection:
            # A short owner lock prevents a READ COMMITTED multi-query read from
            # observing payload/events and control position from different commits.
            self.store.lock(connection, key)
            return self._read(connection, principal, key)

    def _lease(self, connection, principal, lease):
        key = self.store.lease_key(connection, principal, lease)
        self.store.lock(connection, key)
        require(connection.execute(text("SELECT 1 FROM planning.trace_publication_control WHERE " + LEASE), key)
                .first() is not None, "publication_lease_lost")
        return key

    @staticmethod
    def _append(connection, key, previous_position, event):
        next_position = previous_position + 1
        connection.execute(text("INSERT INTO planning.trace_publication_events "
            "(tenant_id,project_id,publication_id,position,event_sha256,canonical_bytes) "
            "VALUES (:tenant,:project,:publication,:next,:digest,:content)"),
            {**key, "next": next_position, "digest": event.sha256, "content": event.canonical})
        updated = connection.execute(text("UPDATE planning.trace_publication_control SET position=:next WHERE " +
            LEASE + " AND position=:previous"), {**key, "next": next_position, "previous": previous_position})
        # Check DB clock at the actual position write too. Failed fencing rolls
        # back the new payload/event in this transaction.
        require(updated.rowcount == 1, "publication_lease_or_position_lost")

    def prepare(self, principal, lease, review):
        with self.store.engine.begin() as connection:
            key = self._lease(connection, principal, lease)
            state = self._read(connection, principal, key)
            require(state is not None, "publication_unknown")
            projection, task = self._facts(connection, principal, state.identity)
            require(review.task.canonical == task.canonical, "publication_task_binding")
            artifact = TraceArtifact.reviewed(state.identity, projection, review, schema=self.store.schema)
            payload = PayloadRecord(artifact, ReviewRecord.from_review(review))
            if state.payload is not None:
                require(state.payload == payload, "publication_payload_conflict")
                return state
            require(len(payload.manifest) <= 262144, "publication_manifest_size")
            connection.execute(text("INSERT INTO planning.trace_publication_payloads "
                "(tenant_id,project_id,publication_id,trace_bytes,review_bytes,manifest_bytes,payload_sha256) "
                "VALUES (:tenant,:project,:publication,:body,:review,:manifest,:digest)"),
                {**key, "body": artifact.body, "review": payload.review.canonical,
                 "manifest": payload.manifest, "digest": payload.sha256})
            event = PublicationEvent.record(1, PublicationAttempt.first(state.identity), "prepared", None)
            self._append(connection, key, 0, event)
            return self._read(connection, principal, key)

    def advance(self, principal, lease, expected_position, action, data=None):
        require(type(expected_position) is int and 1 <= expected_position <= 64, "publication_event_position")
        with self.store.engine.begin() as connection:
            key = self._lease(connection, principal, lease)
            state = self._read(connection, principal, key)
            require(state is not None and state.payload is not None, "publication_payload_pending")
            require(state.position == expected_position, "publication_position_conflict")
            attempt = advance(state.attempt, action, data, state.identity, state.payload.artifact)
            event = PublicationEvent.record(state.position + 1, attempt, action, data)
            # Validate the complete durable encoding before the first write.
            require(event.apply(state.attempt, state.identity, state.payload.artifact, state.position + 1) == attempt,
                    "publication_event_projection")
            self._append(connection, key, state.position, event)
            return self._read(connection, principal, key)
