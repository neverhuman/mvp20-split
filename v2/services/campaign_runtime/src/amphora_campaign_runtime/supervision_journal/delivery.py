"""Database-clock ownership and bounded append-only outgoing delivery evidence."""

from datetime import timedelta

from sqlalchemy import text

from ..supervision_requests.binding import encoded
from ..supervision_responses import SupervisionReceiptObservation
from ..supervision_scope.observations import digest, require
from .delivery_values import DeliveryEvent, evidence_type, fingerprint, identifier
from .storage import SELECT, RequestJournal, StoredRequest, outgoing

KEY = 'tenant_id=:tenant AND project_id=:project AND run_id=:run AND decision_id=:decision AND request_sha256=:request'
TERMINAL = {'recorded', 'rejected', 'failed', 'expired'}


class DeliveryJournal:
    def __init__(self, requests: RequestJournal):
        self.requests = requests

    def _open(self, conn, principal, reference, request_sha256):
        principal.require('supervise_dispatch')
        require(principal.scope == reference.scope, 'delivery_scope_mismatch')
        params = {**self.requests.params(principal, reference.run_id, reference.decision_id),
                  'request': digest(request_sha256)}
        self.requests.leases._run(conn, params)
        row = conn.execute(text(SELECT + ' AND r.request_sha256=:request'), params).mappings().one_or_none()
        require(row is not None, 'supervision_request_unavailable')
        original = StoredRequest.from_row(row)
        require(original.frame.document().prepared_by == principal.actor_id, 'delivery_holder_mismatch')
        conn.execute(text('INSERT INTO runtime.supervision_delivery '
            '(tenant_id,project_id,run_id,decision_id,request_sha256) '
            'VALUES (:tenant,:project,:run,:decision,:request) ON CONFLICT DO NOTHING'), params)
        control = conn.execute(text('SELECT * FROM runtime.supervision_delivery WHERE ' + KEY +
                                    ' FOR UPDATE'), params).mappings().one()
        return params, original, control

    @staticmethod
    def _existing(conn, params, event_id, submission):
        row = conn.execute(text('SELECT * FROM runtime.supervision_delivery_events WHERE ' + KEY +
            ' AND event_id=:event'), {**params, 'event': identifier(event_id)}).mappings().one_or_none()
        return None if row is None else DeliveryEvent.from_row(row).replay(submission)

    @staticmethod
    def _append(conn, params, control, event_id, kind, evidence, *, claims):
        values = {**params, 'sequence': control['events'] + 1, 'event': event_id, 'kind': kind,
            'fence': evidence.fence, 'evidence': encoded(evidence), 'claims': claims,
            'status': 'leased' if kind == 'claim' else kind if kind in TERMINAL else 'pending',
            'holder': evidence.holder if kind == 'claim' else None,
            'expires': evidence.expires_at if kind == 'claim' else None}
        row = conn.execute(text('INSERT INTO runtime.supervision_delivery_events '
            '(tenant_id,project_id,run_id,decision_id,request_sha256,sequence,event_id,fence,kind,evidence) '
            'VALUES (:tenant,:project,:run,:decision,:request,:sequence,:event,:fence,:kind,:evidence) RETURNING *'),
            values).mappings().one()
        conn.execute(text('UPDATE runtime.supervision_delivery SET events=:sequence,claims=:claims,status=:status,'
            'fence=:fence,holder=:holder,expires_at=:expires WHERE ' + KEY), values)
        return DeliveryEvent.from_row(row)

    def claim(self, principal, reference, request_sha256, *, event_id, seconds=60):
        identifier(event_id)
        require(type(seconds) is int and 1 <= seconds <= 300, 'delivery_lease_seconds')
        submission = fingerprint({'kind': 'claim', 'holder': principal.actor_id, 'seconds': seconds})
        def transaction(conn):
            params, original, control = self._open(conn, principal, reference, request_sha256)
            old = self._existing(conn, params, event_id, submission)
            if old is not None:
                return old.lease(reference, request_sha256)
            if control['status'] in TERMINAL:
                return None
            now = conn.execute(text('SELECT clock_timestamp()')).scalar_one()
            if control['status'] == 'leased' and control['expires_at'] > now:
                return None
            deadline = original.frame.request.deadline_unix_ms / 1000
            expired = now.timestamp() >= deadline
            exhausted = control['claims'] >= 16 or control['events'] >= 63 or control['fence'] >= 9007199254740991
            if expired or exhausted:
                evidence = evidence_type(original.frame.request)(submission_sha256=submission, holder=principal.actor_id,
                    fence=control['fence'], expires_at=None,
                    reason='request_deadline' if expired else 'delivery_limit')
                self._append(conn, params, control, event_id, 'expired' if expired else 'failed', evidence,
                             claims=control['claims'])
                return None
            expiry = min(now + timedelta(seconds=seconds), now.fromtimestamp(deadline, tz=now.tzinfo))
            evidence = evidence_type(original.frame.request)(submission_sha256=submission, holder=principal.actor_id,
                fence=control['fence'] + 1, expires_at=expiry)
            result = self._append(conn, params, control, event_id, 'claim', evidence, claims=control['claims'] + 1)
            return result.lease(reference, request_sha256)
        return self.requests.leases.commands.transact(transaction)

    def observe(self, principal, lease, *, event_id, receipt=None, readback=None, reason=None):
        identifier(event_id)
        require((receipt is None and reason is not None and readback is None) or
                (receipt is not None and reason is None), 'delivery_observation_shape')
        if reason is not None:
            identifier(reason)
        submission = fingerprint({'lease': lease.record, 'reason': reason,
            'receipt': None if receipt is None else receipt.model_dump(mode='json'),
            'readback': None if readback is None else readback.model_dump(mode='json')})
        def transaction(conn):
            params, original, control = self._open(conn, principal, lease.reference, lease.request_sha256)
            old = self._existing(conn, params, event_id, submission)
            if old is not None:
                return old
            now = conn.execute(text('SELECT clock_timestamp()')).scalar_one()
            require(control['status'] == 'leased' and control['holder'] == lease.holder == principal.actor_id and
                    control['fence'] == lease.fence and control['expires_at'] == lease.expires_at and
                    now < lease.expires_at, 'delivery_lease_lost')
            observed = None
            if receipt is not None:
                previous = self._previous(conn, params)
                command = outgoing(original.frame, original.canonical_command)
                observed = SupervisionReceiptObservation.observe(command, receipt, readback=readback, previous=previous)
            kind = 'unknown' if observed is None else observed.status
            final_reason = reason
            if control['events'] >= 63 and kind not in TERMINAL:
                kind, final_reason = 'failed', 'delivery_event_limit'
            evidence = evidence_type(original.frame.request)(submission_sha256=submission, holder=lease.holder, fence=lease.fence,
                expires_at=lease.expires_at, reason=final_reason,
                receipt=None if observed is None else observed.document(),
                readback=None if observed is None or observed.readback_canonical is None else
                    type(original.frame.request).model_validate_json(observed.readback_canonical))
            return self._append(conn, params, control, event_id, kind, evidence, claims=control['claims'])
        return self.requests.leases.commands.transact(transaction)

    @staticmethod
    def _previous(conn, params):
        rows = conn.execute(text('SELECT * FROM runtime.supervision_delivery_events WHERE ' + KEY +
                                  ' ORDER BY sequence DESC'), params).mappings().all()
        for row in rows:
            evidence = DeliveryEvent.from_row(row).evidence
            if evidence.receipt is not None:
                return SupervisionReceiptObservation(encoded(evidence.receipt),
                    None if evidence.readback is None else encoded(evidence.readback))
        return None

    def history(self, principal, reference, request_sha256):
        principal.require('read')
        require(principal.scope == reference.scope, 'delivery_scope_mismatch')
        params = {**self.requests.params(principal, reference.run_id, reference.decision_id),
                  'request': digest(request_sha256)}
        with self.requests.engine.connect() as conn:
            rows = conn.execute(text('SELECT * FROM runtime.supervision_delivery_events WHERE ' + KEY +
                                      ' ORDER BY sequence'), params).mappings().all()
        return tuple(DeliveryEvent.from_row(row) for row in rows)
