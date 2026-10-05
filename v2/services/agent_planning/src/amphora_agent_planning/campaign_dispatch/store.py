"""Immutable handoff selection and DB-clock leases; no peer I/O or dispatch."""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_core import Identifier
from pydantic import TypeAdapter
from sqlalchemy import text

from ..context.policy import require
from .history import CompilerHistory
from .selection import CompilerSelection

KEY = 'tenant_id=:tenant AND project_id=:project AND selection_id=:selection'
LEASE = KEY + ' AND holder=:holder AND fence=:fence AND expires_at>clock_timestamp()'


@dataclass(frozen=True)
class StoredCompilerSelection:
    selection: CompilerSelection
    registered_at: datetime


@dataclass(frozen=True)
class CompilerLease:
    selection: CompilerSelection
    holder: str
    fence: int
    expires_at: datetime


class CompilerStore:
    def __init__(self, engine, runtime_owner, runtime_actor, eligibility):
        for value in (runtime_owner, runtime_actor):
            TypeAdapter(Identifier).validate_python(value, strict=True)
        eligibility.verify()
        self.engine, self.runtime_owner, self.runtime_actor, self.eligibility = engine, runtime_owner, runtime_actor, eligibility

    @staticmethod
    def key(principal, identifier):
        TypeAdapter(Identifier).validate_python(identifier, strict=True)
        return {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id, 'selection': identifier}

    @staticmethod
    def lock(connection, key):
        token = json.dumps(['planning.compiler-selection.v1', key['tenant'], key['project'], key['selection']])
        connection.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:token,0))'), {'token': token})

    def checked(self, principal, selection):
        selection = CompilerSelection.restore(selection.canonical, principal)
        value = selection.document()
        require(value.runtime.owner_id == self.runtime_owner and value.runtime.actor_id == self.runtime_actor and
                value.witness.eligibility_json.encode() == self.eligibility.canonical, 'compiler_configuration_conflict')
        return selection

    def selection(self, connection, principal, key):
        row = connection.execute(text('SELECT * FROM planning.compiler_selections WHERE ' + KEY), key).mappings().first()
        if row is None:
            return None
        selected = self.checked(principal, CompilerSelection(bytes(row['canonical_bytes'])))
        value, reference = selected.document(), selected.document().origin.attempt
        require(selected.effect_id == key['selection'] and selected.sha256 == row['selection_sha256'] and
                value.actor_id == row['actor_id'] and reference.engagement.engagement_id == row['engagement_id'] and
                reference.request_sha256 == row['request_sha256'] and reference.ordinal == row['ordinal'],
                'stored_compiler_selection')
        return StoredCompilerSelection(selected, row['registered_at'])

    def register(self, principal, selection):
        selected = self.checked(principal, selection)
        principal.require('record_attempts', selected.document().origin.attempt.engagement.scope)
        # All origin rows are immutable. Load outside the short mutation
        # transaction; no remote owner or processing checks occur here.
        CompilerHistory.load(self.engine, principal, selected)
        key = self.key(principal, selected.effect_id)
        with self.engine.begin() as connection:
            self.lock(connection, key)
            existing = self.selection(connection, principal, key)
            if existing is not None:
                require(existing.selection == selected, 'compiler_selection_conflict')
                return existing
            reference = selected.document().origin.attempt
            connection.execute(text('INSERT INTO planning.compiler_selections '
                '(tenant_id,project_id,selection_id,actor_id,engagement_id,request_sha256,ordinal,selection_sha256,canonical_bytes) '
                'VALUES (:tenant,:project,:selection,:actor,:engagement,:request,:ordinal,:digest,:body)'), key | {
                    'actor': principal.actor_id, 'engagement': reference.engagement.engagement_id,
                    'request': reference.request_sha256, 'ordinal': reference.ordinal, 'digest': selected.sha256, 'body': selected.canonical})
            connection.execute(text('INSERT INTO planning.compiler_control (tenant_id,project_id,selection_id) '
                                    'VALUES (:tenant,:project,:selection)'), key)
            return self.selection(connection, principal, key)

    def read(self, principal, identifier):
        principal.require('read_attempts', principal.scope)
        with self.engine.connect() as connection:
            result = self.selection(connection, principal, self.key(principal, identifier))
        if result is not None:
            CompilerHistory.load(self.engine, principal, result.selection)
        return result

    @staticmethod
    def seconds(value):
        require(type(value) is int and 1 <= value <= 300, 'compiler_lease_seconds')

    def acquire(self, principal, identifier, seconds=30):
        principal.require('record_attempts', principal.scope)
        self.seconds(seconds)
        key = self.key(principal, identifier)
        with self.engine.begin() as connection:
            self.lock(connection, key)
            selected = self.selection(connection, principal, key)
            require(selected is not None, 'compiler_selection_unknown')
            holder = uuid.uuid4().hex
            row = connection.execute(text('UPDATE planning.compiler_control SET holder=:holder,fence=fence+1,'
                "expires_at=clock_timestamp()+(:seconds * interval '1 second') WHERE " + KEY +
                ' AND (expires_at IS NULL OR expires_at<=clock_timestamp()) AND fence<9007199254740991 '
                'RETURNING fence,expires_at'), key | {'holder': holder, 'seconds': seconds}).mappings().first()
            require(row is not None, 'compiler_lease_unavailable')
            return CompilerLease(selected.selection, holder, row['fence'], row['expires_at'])

    def lease_key(self, connection, principal, lease):
        principal.require('record_attempts', lease.selection.document().origin.attempt.engagement.scope)
        key = self.key(principal, lease.selection.effect_id)
        actual = self.selection(connection, principal, key)
        require(actual is not None and actual.selection == lease.selection, 'compiler_lease_identity')
        return key | {'holder': lease.holder, 'fence': lease.fence}

    def guard(self, principal, lease):
        with self.engine.connect() as connection:
            key = self.lease_key(connection, principal, lease)
            require(connection.execute(text('SELECT 1 FROM planning.compiler_control WHERE ' + LEASE), key).first() is not None,
                    'compiler_lease_lost')

    def renew(self, principal, lease, seconds=30):
        self.seconds(seconds)
        with self.engine.begin() as connection:
            key = self.lease_key(connection, principal, lease)
            self.lock(connection, key)
            expiry = connection.execute(text('UPDATE planning.compiler_control SET '
                "expires_at=clock_timestamp()+(:seconds * interval '1 second') WHERE " + LEASE + ' RETURNING expires_at'),
                key | {'seconds': seconds}).scalar_one_or_none()
            require(expiry is not None, 'compiler_lease_lost')
            return CompilerLease(lease.selection, lease.holder, lease.fence, expiry)

    def release(self, principal, lease):
        with self.engine.begin() as connection:
            key = self.lease_key(connection, principal, lease)
            self.lock(connection, key)
            changed = connection.execute(text('UPDATE planning.compiler_control SET holder=NULL,expires_at=NULL WHERE ' + LEASE), key)
            require(changed.rowcount == 1, 'compiler_lease_lost')

    def fence_write(self, connection, principal, lease):
        """Final linearization check inside the caller's locked transaction."""
        key = self.lease_key(connection, principal, lease)
        changed = connection.execute(text('UPDATE planning.compiler_control SET fence=fence WHERE ' + LEASE), key)
        require(changed.rowcount == 1, 'compiler_lease_lost')
