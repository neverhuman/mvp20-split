"""Immutable intents and observations; no call dispatch or budget authority yet."""

import json

from sqlalchemy import text

from ..context import RequestSnapshot
from ..context.policy import require
from .execution_state import require_execution_open
from .family_state import lock_request
from .records import AttemptJournal, request_from_row, verified_observation

KEY = "tenant_id=:tenant AND project_id=:project AND engagement_id=:engagement"


class PlanningJournal:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def _key(reference):
        return {"tenant": reference.scope.tenant_id, "project": reference.scope.project_id,
                "engagement": reference.engagement_id}

    @staticmethod
    def _lock(connection, key):
        token = json.dumps(["planning.request.v1", key["tenant"], key["project"], key["engagement"]])
        connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:token,0))"), {"token": token})

    @staticmethod
    def _request(connection, key, principal):
        row = connection.execute(text("SELECT * FROM planning.requests WHERE " + KEY), key).mappings().first()
        return request_from_row(row, principal) if row else None

    @staticmethod
    def _attempt(connection, key, snapshot):
        attempt = connection.execute(text("SELECT * FROM planning.attempts WHERE " + KEY +
            " AND ordinal=:ordinal"), key).mappings().first()
        if attempt is None:
            return None
        observation = connection.execute(text("SELECT * FROM planning.observations WHERE " + KEY +
            " AND ordinal=:ordinal"), key).mappings().first()
        return AttemptJournal.from_rows(snapshot, attempt, observation)

    def register(self, principal, snapshot):
        request = snapshot.document()
        principal.require("record_requests", request.reference.scope)
        snapshot = RequestSnapshot.bind(request, actor_id=principal.actor_id, scope=principal.scope)
        key = self._key(request.reference)
        with self.engine.begin() as connection:
            self._lock(connection, key)
            existing = self._request(connection, key, principal)
            if existing:
                require(existing.canonical == snapshot.canonical, "request_conflict")
                return existing
            connection.execute(text("INSERT INTO planning.requests "
                "(tenant_id,project_id,engagement_id,actor_id,request_sha256,canonical_bytes) "
                "VALUES (:tenant,:project,:engagement,:actor,:digest,:content)"),
                {**key, "actor": principal.actor_id, "digest": snapshot.sha256, "content": snapshot.canonical})
        return snapshot

    def read_request(self, principal, reference):
        principal.require("read_attempts", reference.scope)
        with self.engine.connect() as connection:
            return self._request(connection, self._key(reference), principal)

    def begin_attempt(self, principal, binding):
        reference = binding.reference()
        principal.require("record_attempts", reference.engagement.scope)
        key = {**self._key(reference.engagement), "ordinal": reference.ordinal}
        with self.engine.begin() as connection:
            membership = lock_request(connection, key)
            snapshot = self._request(connection, key, principal)
            require(snapshot is not None, "request_unknown")
            require(snapshot.sha256 == reference.request_sha256, "request_conflict")
            existing = self._attempt(connection, key, snapshot)
            if existing:
                return existing
            require_execution_open(connection, key)
            require(membership is None, "repair_requires_budget_admission")
            latest = connection.execute(text("SELECT COALESCE(MAX(ordinal),0) FROM planning.attempts WHERE " + KEY),
                                         key).scalar_one()
            require(reference.ordinal == latest + 1, "attempt_sequence")
            if latest:
                previous = self._attempt(connection, {**key, "ordinal": latest}, snapshot)
                require(previous.observation is not None, "attempt_pending")
            connection.execute(text("INSERT INTO planning.attempts "
                "(tenant_id,project_id,engagement_id,ordinal,request_sha256) "
                "VALUES (:tenant,:project,:engagement,:ordinal,:digest)"), {**key, "digest": snapshot.sha256})
            return self._attempt(connection, key, snapshot)

    def record(self, principal, binding, observation):
        reference = binding.reference()
        principal.require("record_attempts", reference.engagement.scope)
        observation = verified_observation(binding, observation)
        key = {**self._key(reference.engagement), "ordinal": reference.ordinal}
        with self.engine.begin() as connection:
            lock_request(connection, key)
            snapshot = self._request(connection, key, principal)
            require(snapshot is not None and snapshot.sha256 == reference.request_sha256, "request_conflict")
            return self._record(connection, key, snapshot, binding, observation)

    def _record(self, connection, key, snapshot, binding, observation):
        observation = verified_observation(binding, observation)
        existing = self._attempt(connection, key, snapshot)
        require(existing is not None, "attempt_unknown")
        if existing.observation is not None:
            require(existing.observation == observation, "observation_conflict")
            return existing
        require_execution_open(connection, key)
        connection.execute(text("INSERT INTO planning.observations "
            "(tenant_id,project_id,engagement_id,ordinal,canonical_bytes,capture_bytes) "
            "VALUES (:tenant,:project,:engagement,:ordinal,:content,:capture)"),
            {**key, "content": observation.canonical, "capture": observation.capture.content})
        return self._attempt(connection, key, snapshot)

    def read_attempt(self, principal, reference):
        principal.require("read_attempts", reference.engagement.scope)
        key = {**self._key(reference.engagement), "ordinal": reference.ordinal}
        with self.engine.connect() as connection:
            snapshot = self._request(connection, key, principal)
            if snapshot is None:
                return None
            require(snapshot.sha256 == reference.request_sha256, "request_conflict")
            return self._attempt(connection, key, snapshot)
