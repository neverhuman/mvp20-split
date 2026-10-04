"""Atomic owner preparation and lease-fenced append-only outcome history."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from ..context.policy import require
from ..publication.records import encode
from .events import HandoffEvent, HandoffProgress
from .history import HandoffHistory
from .prepared import PreparedHandoff
from .selection import HandoffSelection
from .store import KEY, LEASE, HandoffStore


@dataclass(frozen=True)
class HandoffState:
    selection: HandoffSelection
    payload: PreparedHandoff | None
    progress: HandoffProgress | None
    position: int
    prepared_at: datetime | None
    events: tuple[tuple[HandoffEvent, datetime], ...]

    @property
    def terminal(self):
        return self.progress is not None and self.progress.terminal


class HandoffJournal:
    def __init__(self, store: HandoffStore):
        self.store = store

    def _read(self, connection, principal, key):
        selected = self.store.selection(connection, principal, key)
        if selected is None:
            return None
        position = connection.execute(text("SELECT position FROM planning.owner_handoff_control WHERE " + KEY), key).scalar_one()
        row = connection.execute(text("SELECT * FROM planning.owner_handoff_payloads WHERE " + KEY), key).mappings().first()
        if row is None:
            require(position == 0, "stored_handoff_position")
            return HandoffState(selected, None, None, 0, None, ())
        history = HandoffHistory.load(connection, principal, selected, self.store.traces)
        payload = PreparedHandoff.restore(row, principal, selected, history)
        rows = connection.execute(text("SELECT * FROM planning.owner_handoff_events WHERE " + KEY +
            " ORDER BY position LIMIT 65"), key).mappings().all()
        require(0 < len(rows) == position <= 64, "stored_handoff_position")
        progress, events = None, []
        for index, row_event in enumerate(rows, 1):
            event = HandoffEvent(bytes(row_event["canonical_bytes"]))
            require(row_event["position"] == index and event.sha256 == row_event["event_sha256"], "stored_handoff_event")
            progress = event.apply(progress, payload.request, index)
            events.append((event, row_event["recorded_at"]))
        return HandoffState(selected, payload, progress, position, row["prepared_at"], tuple(events))

    def read(self, principal, effect_id):
        principal.require("read_attempts", principal.scope)
        key = self.store.key(principal, effect_id)
        with self.store.engine.begin() as connection:
            self.store.lock(connection, key)
            return self._read(connection, principal, key)

    def _lease(self, connection, principal, lease):
        key = self.store.lease_key(connection, principal, lease)
        self.store.lock(connection, key)
        require(connection.execute(text("SELECT 1 FROM planning.owner_handoff_control WHERE " + LEASE), key).first()
                is not None, "handoff_lease_lost")
        return key

    @staticmethod
    def _append(connection, key, previous, event):
        next_position = previous + 1
        connection.execute(text("INSERT INTO planning.owner_handoff_events "
            "(tenant_id,project_id,effect_id,position,event_sha256,canonical_bytes) "
            "VALUES (:tenant,:project,:effect,:next,:digest,:body)"),
            key | {"next": next_position, "digest": event.sha256, "body": event.canonical})
        changed = connection.execute(text("UPDATE planning.owner_handoff_control SET position=:next WHERE " +
            LEASE + " AND position=:previous"), key | {"next": next_position, "previous": previous})
        require(changed.rowcount == 1, "handoff_lease_or_position_lost")

    def prepare(self, principal, lease, review, *, questions=None, knowledge=None):
        with self.store.engine.begin() as connection:
            key = self._lease(connection, principal, lease)
            state = self._read(connection, principal, key)
            require(state is not None, "handoff_unknown")
            history = HandoffHistory.load(connection, principal, state.selection, self.store.traces)
            payload = PreparedHandoff.create(principal, state.selection, history, review, questions=questions, knowledge=knowledge)
            if state.payload is not None:
                require(state.payload == payload, "handoff_payload_conflict")
                return state
            self._dependency(connection, principal, payload, history)
            connection.execute(text("INSERT INTO planning.owner_handoff_payloads "
                "(tenant_id,project_id,effect_id,body_bytes,review_bytes,witness_bytes,manifest_bytes,payload_sha256) "
                "VALUES (:tenant,:project,:effect,:body,:review,:witness,:manifest,:digest)"), key |
                {"body": payload.request.canonical, "review": payload.review.canonical, "witness": payload.witness,
                 "manifest": payload.manifest, "digest": payload.sha256})
            event = HandoffEvent.record(payload.request, 1, "prepared")
            self._append(connection, key, 0, event)
            return self._read(connection, principal, key)

    def advance(self, principal, lease, expected_position, action, data=None):
        require(type(expected_position) is int and 1 <= expected_position < 64, "handoff_event_limit")
        with self.store.engine.begin() as connection:
            key = self._lease(connection, principal, lease)
            state = self._read(connection, principal, key)
            require(state is not None and state.payload is not None and state.position == expected_position,
                    "handoff_position_conflict")
            if action == "dispatch":
                history = HandoffHistory.load(connection, principal, state.selection, self.store.traces)
                self._dependency(connection, principal, state.payload, history)
            event = HandoffEvent.record(state.payload.request, expected_position + 1, action, data)
            event.apply(state.progress, state.payload.request, expected_position + 1)
            self._append(connection, key, expected_position, event)
            return self._read(connection, principal, key)

    def _dependency(self, connection, principal, payload, history):
        dependency = payload.dependency(history)
        if dependency is None:
            return
        selected, question = dependency
        # Question terminal histories never advance. There is no reverse
        # question-to-need dependency or lock held over a peer operation.
        key = self.store.key(principal, selected.effect_id)
        self.store.lock(connection, key)
        state = self._read(connection, principal, key)
        require(state is not None and state.selection == selected and state.terminal and
                state.progress.state == "acknowledged" and state.payload.request.canonical ==
                encode(question.model_dump(mode="json")), "handoff_dependency_unacknowledged")
