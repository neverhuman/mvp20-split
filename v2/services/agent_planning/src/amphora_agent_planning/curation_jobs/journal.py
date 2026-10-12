"""Fenced short transactions; callers do all external work after commit."""
from dataclasses import dataclass, replace
from datetime import timedelta
from uuid import uuid4
import hashlib

from amphora_contracts_core import Identifier
from pydantic import TypeAdapter
from sqlalchemy import text

from ..context.policy import require
from ..curation_intake.record import OriginalCuration, encoded
from .state import JobProgress

KEY = 'tenant_id=:tenant AND project_id=:project AND curation_id=:curation'


def key_for(principal, curation_id):
    TypeAdapter(Identifier).validate_python(curation_id, strict=True)
    return {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id,
            'curation': curation_id}


def current(conn, original):
    identity = original.incoming.command.identity
    row = conn.execute(text('SELECT * FROM planning.curation_progress WHERE ' + KEY +
        ' ORDER BY revision DESC LIMIT 1'), {'tenant': identity.scope.tenant_id,
        'project': identity.scope.project_id, 'curation': original.incoming.curation_id}).mappings().one_or_none()
    return JobProgress.restore(original, row) if row is not None else None


@dataclass(frozen=True)
class JobLease:
    curation_id: str
    worker_id: str
    fence: str
    progress: JobProgress


class CurationJobs:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def _lock(conn, key):
        conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:token,0))'),
            {'token': 'curation-job:' + key['tenant'] + ':' + key['project'] + ':' + key['curation']})

    @staticmethod
    def _original(conn, principal, key):
        row = conn.execute(text('SELECT * FROM planning.curation_requests WHERE ' + KEY +
            ' AND actor_id=:actor'), {**key, 'actor': principal.actor_id}).mappings().one_or_none()
        return OriginalCuration.restore(row) if row is not None else None

    @staticmethod
    def _append(conn, key, progress):
        raw = encoded(progress.view)
        conn.execute(text('INSERT INTO planning.curation_progress '
            '(tenant_id,project_id,curation_id,revision,view_bytes,view_sha256) '
            'VALUES (:tenant,:project,:curation,:revision,:raw,:digest)'),
            {**key, 'revision': progress.view.receipt.revision, 'raw': raw,
             'digest': hashlib.sha256(raw).hexdigest()})

    def claim(self, principal, curation_id, worker_id, *, lease_seconds=30):
        principal.require('execute_curations', principal.scope)
        TypeAdapter(Identifier).validate_python(worker_id, strict=True)
        require(type(lease_seconds) is int and 1 <= lease_seconds <= 60, 'curation_lease_bound')
        key = key_for(principal, curation_id)
        with self.engine.begin() as conn:
            self._lock(conn, key)
            original = self._original(conn, principal, key)
            if original is None:
                return None
            progress = current(conn, original)
            if progress is not None and progress.terminal:
                return None
            now = conn.execute(text('SELECT clock_timestamp()')).scalar_one()
            row = conn.execute(text('SELECT * FROM planning.curation_leases WHERE ' + KEY), key).mappings().one_or_none()
            if row is not None and row['lease_until'] > now:
                return None
            if progress is None:
                progress = JobProgress.initial(original, now)
                self._append(conn, key, progress)
            fence = uuid4().hex
            conn.execute(text('INSERT INTO planning.curation_leases '
                '(tenant_id,project_id,curation_id,worker_id,fence,lease_until) '
                'VALUES (:tenant,:project,:curation,:worker,:fence,:until) '
                'ON CONFLICT (tenant_id,project_id,curation_id) DO UPDATE SET '
                'worker_id=EXCLUDED.worker_id,fence=EXCLUDED.fence,lease_until=EXCLUDED.lease_until'),
                {**key, 'worker': worker_id, 'fence': fence, 'until': now + timedelta(seconds=lease_seconds)})
            return JobLease(curation_id, worker_id, fence, progress)

    def _owned(self, conn, principal, lease, key):
        self._lock(conn, key)
        original = self._original(conn, principal, key)
        require(original is not None, 'curation_lease_unavailable')
        now = conn.execute(text('SELECT clock_timestamp()')).scalar_one()
        row = conn.execute(text('SELECT * FROM planning.curation_leases WHERE ' + KEY), key).mappings().one_or_none()
        require(row is not None and row['worker_id'] == lease.worker_id
                and row['fence'] == lease.fence and row['lease_until'] > now,
                'curation_lease_lost')
        progress = current(conn, original)
        require(progress is not None and not progress.terminal, 'curation_job_terminal')
        require(progress.view.receipt.revision == lease.progress.view.receipt.revision,
                'curation_progress_conflict')
        return progress, now

    def heartbeat(self, principal, lease, *, lease_seconds=30):
        principal.require('execute_curations', principal.scope)
        require(type(lease_seconds) is int and 1 <= lease_seconds <= 60, 'curation_lease_bound')
        key = key_for(principal, lease.curation_id)
        with self.engine.begin() as conn:
            _, now = self._owned(conn, principal, lease, key)
            conn.execute(text('UPDATE planning.curation_leases SET lease_until=:until WHERE ' + KEY),
                         {**key, 'until': now + timedelta(seconds=lease_seconds)})

    def fail(self, principal, lease, reason):
        principal.require('execute_curations', principal.scope)
        key = key_for(principal, lease.curation_id)
        with self.engine.begin() as conn:
            progress, now = self._owned(conn, principal, lease, key)
            result = progress.fail(reason, now)
            self._append(conn, key, result)
            return result.view


    def refresh(self, principal, lease, *, lease_seconds=60):
        """Renew this exact fence against current progress, including concurrent steps."""
        principal.require('execute_curations', principal.scope)
        require(type(lease_seconds) is int and 1 <= lease_seconds <= 60, 'curation_lease_bound')
        key = key_for(principal, lease.curation_id)
        with self.engine.begin() as conn:
            self._lock(conn, key)
            original = self._original(conn, principal, key)
            require(original is not None, 'curation_lease_unavailable')
            progress = current(conn, original)
            require(progress is not None, 'curation_progress_missing')
            updated = replace(lease, progress=progress)
            if progress.terminal:
                return updated  # Read-only final progress; never renew a closed job.
            _, now = self._owned(conn, principal, updated, key)
            conn.execute(text('UPDATE planning.curation_leases SET lease_until=:until WHERE ' + KEY),
                {**key, 'until': now + timedelta(seconds=lease_seconds)})
            return updated

    def release(self, principal, lease):
        """Graceful release changes only coordination; a replaced fence is a no-op."""
        principal.require('execute_curations', principal.scope)
        key = key_for(principal, lease.curation_id)
        with self.engine.begin() as conn:
            self._lock(conn, key)
            require(self._original(conn, principal, key) is not None, 'curation_lease_unavailable')
            changed = conn.execute(text('UPDATE planning.curation_leases SET lease_until=clock_timestamp() '
                'WHERE ' + KEY + ' AND worker_id=:worker AND fence=:fence RETURNING fence'),
                {**key, 'worker': lease.worker_id, 'fence': lease.fence}).scalar_one_or_none()
            return changed is not None
