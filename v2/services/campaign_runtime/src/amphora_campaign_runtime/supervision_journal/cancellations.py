"""Immutable cancellation requests; recording never selects an execution winner."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_supervision import (
    CancelSupervision,
    SupervisionCommandReceipt,
    parse_supervision_command,
)
from sqlalchemy import text

from ..persistence.commands import WHERE, TerminalDisposition, _bindings
from ..supervision_requests.binding import encoded
from ..supervision_scope.observations import require
from .frames import RequestFrame
from .responses import ResponseJournal


@dataclass(frozen=True)
class Cancellation:
    canonical: bytes

    @classmethod
    def bind(cls, frame, value, actor):
        record = CancelSupervision.model_validate_json(value.model_dump_json())
        require(actor in {frame.document().prepared_by, frame.request.planning_request.actor_id}, 'cancellation_actor_mismatch')
        require(record.reference == frame.request.reference and record.request_sha256 == frame.request_sha256,
                'cancellation_request_mismatch')
        return cls(encoded(record))

    def document(self):
        return CancelSupervision.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()

    def receipt(self, command, operation, reason=None):
        outcome = {'status': 'rejected' if reason else 'recorded', 'binding': {
            'identity': command.identity.model_dump(mode='json'), 'request_sha256': command.sha256,
            'operation_id': operation}}
        if reason:
            outcome['reason_code'] = reason
        else:
            outcome['committed'] = {'kind': 'cancellation', 'object_id': self.document().cancellation_id,
                                    'revision': 1, 'content_sha256': self.sha256}
        return SupervisionCommandReceipt.model_validate_json(json.dumps({'outcome': outcome}))


@dataclass(frozen=True)
class StoredCancellation:
    bound: Cancellation
    actor_id: str
    operation_id: str
    sequence: int
    created_at: datetime


class CancellationJournal:
    def __init__(self, requests):
        self.requests = requests

    @staticmethod
    def checked(command):
        require(parse_supervision_command('runtime.supervision.cancel', command.canonical_bytes) == command,
                'cancellation_command_mismatch')
        return CancelSupervision.model_validate_json(json.dumps(json.loads(command.canonical_bytes)['payload']))

    def record(self, principal, command):
        value = self.checked(command)
        principal.require('supervise_cancel', command.identity)
        params = {**self.requests.params(principal, value.reference.run_id, value.reference.decision_id),
                  'request': value.request_sha256, 'cancellation': value.cancellation_id}
        with self.requests.engine.connect() as conn:
            frame = ResponseJournal._origin(conn, params)
        bound = Cancellation.bind(frame, value, principal.actor_id)
        registration = self.requests.leases.commands.register(command)

        def transaction(conn):
            self.requests.leases._run(conn, params)
            prior = conn.execute(text('SELECT status,receipt FROM runtime.commands WHERE ' + WHERE),
                                 _bindings(command)).mappings().one()
            if prior['status'] != 'pending':
                return SupervisionCommandReceipt.model_validate_json(json.dumps(prior['receipt']))
            existing = conn.execute(text('SELECT 1 FROM runtime.supervision_cancellations WHERE '
                'tenant_id=:tenant AND project_id=:project AND cancellation_id=:cancellation'), params).first()
            count = conn.execute(text('SELECT count(*) FROM runtime.supervision_cancellations WHERE '
                'tenant_id=:tenant AND project_id=:project AND run_id=:run AND decision_id=:decision '
                'AND request_sha256=:request'), params).scalar_one()
            reason = 'cancellation_identity_conflict' if existing else 'cancellation_history_limit' if count >= 16 else None
            if reason is None:
                conn.execute(text('''INSERT INTO runtime.supervision_cancellations
                    (tenant_id,project_id,run_id,decision_id,request_sha256,cancellation_id,sequence,
                     cancellation_sha256,canonical_cancellation,actor_id,operation_id) VALUES
                    (:tenant,:project,:run,:decision,:request,:cancellation,:sequence,:digest,:canonical,:actor,:operation)'''),
                    {**params, 'sequence': count + 1, 'digest': bound.sha256, 'canonical': bound.canonical,
                     'actor': principal.actor_id, 'operation': registration.operation_id})
            receipt = bound.receipt(command, registration.operation_id, reason)
            self.requests.leases.commands.finish(conn, command,
                TerminalDisposition('rejected' if reason else 'accepted', receipt.model_dump_json().encode()))
            return receipt
        return self.requests.leases.commands.transact(transaction)

    def cancellation(self, principal, cancellation_id):
        principal.require('read')
        with self.requests.engine.connect() as conn:
            row = conn.execute(text('''SELECT c.*,r.canonical_frame FROM runtime.supervision_cancellations c
                JOIN runtime.supervision_requests r USING(tenant_id,project_id,run_id,decision_id,request_sha256)
                WHERE c.tenant_id=:tenant AND c.project_id=:project AND c.cancellation_id=:cancellation'''),
                {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id,
                 'cancellation': cancellation_id}).mappings().one_or_none()
        if row is None:
            return None
        frame = RequestFrame.from_bytes(bytes(row['canonical_frame']))
        bound = Cancellation.bind(frame, CancelSupervision.model_validate_json(bytes(row['canonical_cancellation'])), row['actor_id'])
        value = bound.document()
        require(bound.canonical == bytes(row['canonical_cancellation']) and bound.sha256 == row['cancellation_sha256'] and
                value.cancellation_id == row['cancellation_id'] and value.request_sha256 == row['request_sha256'] and
                value.reference.run_id == row['run_id'] and value.reference.decision_id == row['decision_id'] and
                value.reference.scope == principal.scope, 'stored_cancellation_mismatch')
        return StoredCancellation(bound, row['actor_id'], row['operation_id'], row['sequence'], row['created_at'])

    def receipt(self, principal, command):
        self.checked(command)
        principal.require('read', command.identity)
        with self.requests.engine.connect() as conn:
            row = conn.execute(text('SELECT profile,request_sha256,canonical_bytes,status,receipt FROM runtime.commands WHERE ' + WHERE),
                               _bindings(command)).mappings().one_or_none()
        if row is None:
            return None
        require(row['profile'] == command.profile and row['request_sha256'] == command.sha256 and
                bytes(row['canonical_bytes']) == command.canonical_bytes, 'cancellation_command_mismatch')
        return None if row['status'] == 'pending' else SupervisionCommandReceipt.model_validate_json(json.dumps(row['receipt']))
