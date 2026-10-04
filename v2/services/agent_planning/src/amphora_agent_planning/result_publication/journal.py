"""Atomic result preparation and lease-fenced append-only upload history."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from ..context.policy import require
from ..publication.attempt import PublicationAttempt
from ..publication.records import advance
from .events import ResultEvent
from .history import ResultHistory
from .prepared import PreparedResult
from .selection import ResultSelection
from .store import KEY, LEASE, ResultStore


@dataclass(frozen=True)
class ResultState:
    selection: ResultSelection
    payload: PreparedResult | None
    attempt: PublicationAttempt | None
    position: int
    prepared_at: datetime | None
    events: tuple[tuple[ResultEvent, datetime], ...]

    @property
    def identity(self):
        return None if self.payload is None else self.payload.identity


class ResultJournal:
    def __init__(self, store: ResultStore):
        self.store = store

    def _read(self, connection, principal, key):
        selected = self.store.selection(connection, principal, key)
        if selected is None:
            return None
        position = connection.execute(text("SELECT position FROM planning.result_publication_control WHERE " + KEY), key).scalar_one()
        row = connection.execute(text("SELECT * FROM planning.result_publication_payloads WHERE " + KEY), key).mappings().first()
        if row is None:
            require(position == 0, "stored_result_position")
            return ResultState(selected, None, None, 0, None, ())
        history = ResultHistory.load(connection, principal, selected, self.store.traces)
        payload = PreparedResult.restore(row, principal, selected, history)
        rows = connection.execute(text("SELECT * FROM planning.result_publication_events WHERE " + KEY +
            " ORDER BY position LIMIT 65"), key).mappings().all()
        require(0 < len(rows) == position <= 64, "stored_result_position")
        attempt, events = None, []
        for index, row_event in enumerate(rows, 1):
            event = ResultEvent(bytes(row_event["canonical_bytes"]))
            require(row_event["position"] == index and event.sha256 == row_event["event_sha256"], "stored_result_event")
            attempt = event.apply(attempt, payload.identity, payload.artifact, index)
            events.append((event, row_event["recorded_at"]))
        return ResultState(selected, payload, attempt, position, row["prepared_at"], tuple(events))

    def read(self, principal, publication_id):
        principal.require("read_attempts", principal.scope)
        key = self.store.key(principal, publication_id)
        with self.store.engine.begin() as connection:
            self.store.lock(connection, key)
            return self._read(connection, principal, key)

    def _lease(self, connection, principal, lease):
        key = self.store.lease_key(connection, principal, lease)
        self.store.lock(connection, key)
        require(connection.execute(text("SELECT 1 FROM planning.result_publication_control WHERE " + LEASE), key).first()
                is not None, "result_lease_lost")
        return key

    @staticmethod
    def _append(connection, key, previous, event):
        next_position = previous + 1
        connection.execute(text("INSERT INTO planning.result_publication_events "
            "(tenant_id,project_id,publication_id,position,event_sha256,canonical_bytes) "
            "VALUES (:tenant,:project,:publication,:next,:digest,:body)"),
            key | {"next": next_position, "digest": event.sha256, "body": event.canonical})
        changed = connection.execute(text("UPDATE planning.result_publication_control SET position=:next WHERE " +
            LEASE + " AND position=:previous"), key | {"next": next_position, "previous": previous})
        require(changed.rowcount == 1, "result_lease_or_position_lost")

    def prepare(self, principal, lease, review, *, questions=None, feedback=None):
        with self.store.engine.begin() as connection:
            key = self._lease(connection, principal, lease)
            state = self._read(connection, principal, key)
            require(state is not None, "result_unknown")
            history = ResultHistory.load(connection, principal, state.selection, self.store.traces)
            payload = PreparedResult.create(principal, state.selection, history, review, questions=questions, feedback=feedback)
            if state.payload is not None:
                require(state.payload == payload, "result_payload_conflict")
                return state
            connection.execute(text("INSERT INTO planning.result_publication_payloads "
                "(tenant_id,project_id,publication_id,body_bytes,review_bytes,question_bytes,manifest_bytes,payload_sha256) "
                "VALUES (:tenant,:project,:publication,:body,:review,:questions,:manifest,:digest)"), key |
                {"body": payload.artifact.body, "review": payload.review.canonical, "questions": payload.questions,
                 "manifest": payload.manifest, "digest": payload.sha256})
            event = ResultEvent.record(1, PublicationAttempt.first(payload.identity), "prepared", None)
            self._append(connection, key, 0, event)
            return self._read(connection, principal, key)

    def advance(self, principal, lease, expected_position, action, data=None):
        require(type(expected_position) is int and 1 <= expected_position < 64, "result_event_limit")
        with self.store.engine.begin() as connection:
            key = self._lease(connection, principal, lease)
            state = self._read(connection, principal, key)
            require(state is not None and state.payload is not None and state.position == expected_position,
                    "result_position_conflict")
            attempt = advance(state.attempt, action, data, state.payload.identity, state.payload.artifact)
            event = ResultEvent.record(expected_position + 1, attempt, action, data)
            require(event.apply(state.attempt, state.identity, state.payload.artifact, expected_position + 1) == attempt,
                    "result_event_binding")
            self._append(connection, key, expected_position, event)
            return self._read(connection, principal, key)
