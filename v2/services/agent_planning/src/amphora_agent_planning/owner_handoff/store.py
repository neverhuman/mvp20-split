"""Owned handoff selections and DB-clock controls; no peer I/O under SQL."""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_core import Identifier
from pydantic import TypeAdapter
from sqlalchemy import text

from ..context.policy import require
from ..publication.journal import PublicationJournal
from ..publication.store import PublicationStore
from .history import HandoffHistory
from .selection import HandoffSelection

KEY = "tenant_id=:tenant AND project_id=:project AND effect_id=:effect"
LEASE = KEY + " AND holder=:holder AND fence=:fence AND expires_at>clock_timestamp()"


@dataclass(frozen=True)
class HandoffLease:
    selection: HandoffSelection
    holder: str
    fence: int
    expires_at: datetime


class HandoffStore:
    def __init__(self, engine, owner_id, *, trace_publisher_id):
        for value in (owner_id, trace_publisher_id):
            TypeAdapter(Identifier).validate_python(value, strict=True)
        self.engine, self.owner_id = engine, owner_id
        self.traces = PublicationJournal(PublicationStore(engine, trace_publisher_id))

    @staticmethod
    def key(principal, effect_id):
        TypeAdapter(Identifier).validate_python(effect_id, strict=True)
        return {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id,
                "effect": effect_id}

    @staticmethod
    def lock(connection, key):
        token = json.dumps(["planning.owner_handoff.v1", key["tenant"], key["project"], key["effect"]])
        connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:token,0))"), {"token": token})

    def selection(self, connection, principal, key):
        row = connection.execute(text("SELECT * FROM planning.owner_handoffs WHERE " + KEY), key).mappings().first()
        if row is None:
            return None
        selected = HandoffSelection.restore(bytes(row["canonical_bytes"]), principal)
        value, trace = selected.document(), selected.trace()
        require(selected.effect_id == key["effect"] and selected.sha256 == row["selection_sha256"] and
                value["actor_id"] == row["actor_id"] and trace.trace_id == row["trace_id"] and
                trace.sha256 == row["trace_sha256"] and value["interpretation_id"] == row["interpretation_id"],
                "stored_handoff_selection")
        require(value["owner_id"] == row["owner_id"] == self.owner_id, "handoff_configuration_conflict")
        return selected

    def register(self, principal, selection):
        selection = HandoffSelection.restore(selection.canonical, principal)
        principal.require("record_attempts", selection.trace().scope)
        selected = selection.document()
        require(selected["owner_id"] == self.owner_id, "handoff_configuration_conflict")
        key = self.key(principal, selection.effect_id)
        with self.engine.begin() as connection:
            # Initial provenance reads serialize with trace finalization before
            # acquiring the handoff lock. Existing finalized traces never advance.
            self.traces.store.lock(connection, self.traces.store.key(principal, selected["interpretation_id"]))
            self.lock(connection, key)
            existing = self.selection(connection, principal, key)
            if existing is not None:
                require(existing.canonical == selection.canonical, "handoff_selection_conflict")
                return existing
            HandoffHistory.load(connection, principal, selection, self.traces)
            connection.execute(text("INSERT INTO planning.owner_handoffs "
                "(tenant_id,project_id,effect_id,actor_id,trace_id,trace_sha256,interpretation_id,owner_id,"
                "selection_sha256,canonical_bytes) VALUES (:tenant,:project,:effect,:actor,:trace,:trace_digest,"
                ":interpretation,:owner,:digest,:body)"), key | {"actor": principal.actor_id,
                "trace": selection.trace().trace_id, "trace_digest": selection.trace().sha256,
                "interpretation": selected["interpretation_id"], "owner": self.owner_id,
                "digest": selection.sha256, "body": selection.canonical})
            connection.execute(text("INSERT INTO planning.owner_handoff_control "
                "(tenant_id,project_id,effect_id) VALUES (:tenant,:project,:effect)"), key)
        return selection

    @staticmethod
    def seconds(value):
        require(type(value) is int and 1 <= value <= 300, "handoff_lease_seconds")

    def acquire(self, principal, effect_id, seconds=30):
        principal.require("record_attempts", principal.scope)
        self.seconds(seconds)
        key = self.key(principal, effect_id)
        with self.engine.begin() as connection:
            self.lock(connection, key)
            identity = self.selection(connection, principal, key)
            require(identity is not None, "handoff_unknown")
            holder = uuid.uuid4().hex
            row = connection.execute(text("UPDATE planning.owner_handoff_control SET holder=:holder,"
                "fence=fence+1,expires_at=clock_timestamp()+(:seconds * interval '1 second') WHERE " + KEY +
                " AND (expires_at IS NULL OR expires_at<=clock_timestamp()) AND fence<9007199254740991 "
                "RETURNING fence,expires_at"), {**key, "holder": holder, "seconds": seconds}).mappings().first()
            require(row is not None, "handoff_lease_unavailable")
            return HandoffLease(identity, holder, row["fence"], row["expires_at"])

    def lease_key(self, connection, principal, lease):
        principal.require("record_attempts", lease.selection.trace().scope)
        key = self.key(principal, lease.selection.effect_id)
        actual = self.selection(connection, principal, key)
        require(actual is not None and actual.canonical == lease.selection.canonical, "handoff_identity_conflict")
        return {**key, "holder": lease.holder, "fence": lease.fence}

    def guard(self, principal, lease):
        with self.engine.connect() as connection:
            key = self.lease_key(connection, principal, lease)
            require(connection.execute(text("SELECT 1 FROM planning.owner_handoff_control WHERE " + LEASE), key)
                    .first() is not None, "handoff_lease_lost")

    def renew(self, principal, lease, seconds=30):
        self.seconds(seconds)
        with self.engine.begin() as connection:
            key = self.lease_key(connection, principal, lease)
            self.lock(connection, key)
            expires = connection.execute(text("UPDATE planning.owner_handoff_control SET "
                "expires_at=clock_timestamp()+(:seconds * interval '1 second') WHERE " + LEASE + " RETURNING expires_at"),
                {**key, "seconds": seconds}).scalar_one_or_none()
            require(expires is not None, "handoff_lease_lost")
            return HandoffLease(lease.selection, lease.holder, lease.fence, expires)

    def release(self, principal, lease):
        with self.engine.begin() as connection:
            key = self.lease_key(connection, principal, lease)
            self.lock(connection, key)
            result = connection.execute(text("UPDATE planning.owner_handoff_control SET holder=NULL,expires_at=NULL "
                                             "WHERE " + LEASE), key)
            require(result.rowcount == 1, "handoff_lease_lost")
