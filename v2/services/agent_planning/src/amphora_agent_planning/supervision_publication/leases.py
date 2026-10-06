"""Capture-local database clock and fencing; no lock spans a peer call."""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_core import Identifier
from pydantic import TypeAdapter
from sqlalchemy import text

from ..context.policy import require

KEY = 'tenant_id=:tenant AND project_id=:project AND publication_id=:publication'
LIVE = KEY + ' AND holder=:holder AND fence=:fence AND expires_at>clock_timestamp()'


@dataclass(frozen=True)
class CaptureLease:
    publication_id: str
    identity_sha256: str
    holder: str
    fence: int
    expires_at: datetime


def key(principal, publication_id):
    TypeAdapter(Identifier).validate_python(publication_id, strict=True)
    return {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id, 'publication': publication_id}


def lock(conn, params):
    token = json.dumps(['planning.capture_publication.v1', params['tenant'], params['project'], params['publication']])
    conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:token,0))'), {'token': token})


class CaptureLeases:
    def acquire(self, principal, publication_id, seconds=120):
        principal.require('record_attempts', principal.scope)
        require(type(seconds) is int and 1 <= seconds <= 300, 'capture_lease_seconds')
        params = key(principal, publication_id)
        with self.engine.begin() as conn:
            lock(conn, params)
            state = self._read(conn, principal, params)
            require(state is not None, 'capture_unknown')
            holder = uuid.uuid4().hex
            row = conn.execute(text('UPDATE planning.capture_publication_control SET holder=:holder,fence=fence+1,'
                'expires_at=clock_timestamp()+make_interval(secs=>:seconds) WHERE ' + KEY +
                ' AND (expires_at IS NULL OR expires_at<=clock_timestamp()) AND fence<9007199254740991 '
                'RETURNING fence,expires_at'), {**params, 'holder': holder, 'seconds': seconds}).mappings().one_or_none()
            require(row is not None, 'capture_lease_unavailable')
            return CaptureLease(publication_id, state.identity.sha256, holder, row['fence'], row['expires_at'])

    def _lease(self, conn, principal, lease):
        principal.require('record_attempts', principal.scope)
        params = {**key(principal, lease.publication_id), 'holder': lease.holder, 'fence': lease.fence}
        row = conn.execute(text('SELECT actor_id,publisher_id,identity_sha256 FROM planning.capture_publications WHERE ' + KEY),
            params).mappings().one_or_none()
        require(row is not None and row['actor_id'] == principal.actor_id and row['publisher_id'] == self.publisher_id and
            row['identity_sha256'] == lease.identity_sha256, 'capture_lease_identity')
        require(conn.execute(text('SELECT 1 FROM planning.capture_publication_control WHERE ' + LIVE), params).first()
            is not None, 'capture_lease_lost')
        return params

    def guard(self, principal, lease):
        with self.engine.connect() as conn:
            self._lease(conn, principal, lease)

    def release(self, principal, lease):
        with self.engine.begin() as conn:
            params = key(principal, lease.publication_id)
            lock(conn, params)
            params = self._lease(conn, principal, lease)
            changed = conn.execute(text('UPDATE planning.capture_publication_control SET holder=NULL,expires_at=NULL WHERE ' + LIVE), params)
            require(changed.rowcount == 1, 'capture_lease_lost')
