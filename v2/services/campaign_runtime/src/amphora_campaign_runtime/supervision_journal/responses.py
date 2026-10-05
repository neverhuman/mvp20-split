"""Immutable diagnostic/model responses and command receipts; no decision winner."""

import json
from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_supervision import (
    SupervisionCommandReceipt,
    SupervisionResponse,
    parse_supervision_command,
)
from sqlalchemy import text

from ..persistence.commands import WHERE, TerminalDisposition, _bindings
from ..supervision_requests import SupervisionRequestBinding
from ..supervision_responses import SupervisionResponseBinding
from ..supervision_scope.observations import require
from .frames import RequestFrame
from .storage import RequestJournal

RESPONSES = '''SELECT s.*,r.canonical_frame FROM runtime.supervision_responses s
 JOIN runtime.supervision_requests r USING(tenant_id,project_id,run_id,decision_id,request_sha256)
 WHERE s.tenant_id=:tenant AND s.project_id=:project'''


def bind_response(frame, response, capture):
    request = frame.request
    origin = SupervisionRequestBinding.bind(request, frame.footprint(), actor_id=request.planning_request.actor_id)
    return SupervisionResponseBinding.bind(origin, frame.footprint(), response,
        actor_id=request.planning_request.actor_id, capture_bytes=capture)


@dataclass(frozen=True)
class StoredResponse:
    bound: SupervisionResponseBinding
    capture_bytes: bytes | None
    operation_id: str
    sequence: int
    created_at: datetime

    @classmethod
    def from_row(cls, row):
        frame = RequestFrame.from_bytes(bytes(row['canonical_frame']))
        response = SupervisionResponse.model_validate_json(bytes(row['canonical_response']))
        capture = None if row['capture_bytes'] is None else bytes(row['capture_bytes'])
        bound = bind_response(frame, response, capture)
        require(bound.canonical == bytes(row['canonical_response']) and bound.sha256 == row['response_sha256'] and
                response.response_id == row['response_id'] and response.request_sha256 == row['request_sha256'] and
                response.reference.run_id == row['run_id'] and response.reference.decision_id == row['decision_id'] and
                response.reference.scope.tenant_id == row['tenant_id'] and
                response.reference.scope.project_id == row['project_id'], 'stored_response_mismatch')
        return cls(bound, capture, row['operation_id'], row['sequence'], row['created_at'])


@dataclass(frozen=True)
class RecordingReply:
    command: object
    operation_id: str

    def document(self, *, bound=None, reason=None):
        binding = {'identity': self.command.identity.model_dump(mode='json'),
                   'request_sha256': self.command.sha256, 'operation_id': self.operation_id}
        outcome = {'status': 'rejected' if reason else 'recorded', 'binding': binding}
        if reason:
            outcome['reason_code'] = reason
        else:
            outcome['committed'] = {'kind': 'response', 'object_id': bound.document().response_id,
                                    'revision': 1, 'content_sha256': bound.sha256}
        return SupervisionCommandReceipt.model_validate_json(json.dumps({'outcome': outcome}))


class ResponseJournal:
    def __init__(self, requests: RequestJournal):
        self.requests = requests

    def record(self, principal, command, *, capture_bytes):
        checked = parse_supervision_command('runtime.supervision.respond', command.canonical_bytes)
        require(checked == command, 'response_command_mismatch')
        principal.require('supervise_respond', command.identity)
        response = SupervisionResponse.model_validate_json(json.dumps(json.loads(command.canonical_bytes)['payload']))
        params = {**self.requests.params(principal, response.reference.run_id, response.reference.decision_id),
                  'request': response.request_sha256, 'response': response.response_id}
        # Validate exact original capture and configured original actor before creating a command record.
        with self.requests.engine.connect() as conn:
            frame = self._origin(conn, params)
        require(frame.request.planning_request.actor_id == principal.actor_id, 'response_actor_mismatch')
        bound = bind_response(frame, response, capture_bytes)
        registration = self.requests.leases.commands.register(command)
        reply = RecordingReply(command, registration.operation_id)
        def transaction(conn):
            self.requests.leases._run(conn, params)
            previous = conn.execute(text('SELECT status,receipt FROM runtime.commands WHERE ' + WHERE),
                                    _bindings(command)).mappings().one()
            if previous['status'] != 'pending':
                return SupervisionCommandReceipt.model_validate_json(json.dumps(previous['receipt']))
            existing = conn.execute(text(RESPONSES + ' AND s.response_id=:response'), params).mappings().one_or_none()
            count = conn.execute(text('SELECT count(*) FROM runtime.supervision_responses WHERE tenant_id=:tenant '
                'AND project_id=:project AND run_id=:run AND decision_id=:decision AND request_sha256=:request'), params).scalar_one()
            if existing is not None:
                receipt = reply.document(reason='response_identity_conflict')
            elif count >= 64:
                receipt = reply.document(reason='response_history_limit')
            else:
                conn.execute(text('''INSERT INTO runtime.supervision_responses
                    (tenant_id,project_id,run_id,decision_id,request_sha256,response_id,sequence,response_sha256,
                     canonical_response,capture_bytes,operation_id) VALUES
                    (:tenant,:project,:run,:decision,:request,:response,:sequence,:digest,:canonical,:capture,:operation)'''),
                    {**params, 'sequence': count + 1, 'digest': bound.sha256, 'canonical': bound.canonical,
                     'capture': capture_bytes, 'operation': registration.operation_id})
                receipt = reply.document(bound=bound)
            status = 'rejected' if receipt.outcome.status == 'rejected' else 'accepted'
            self.requests.leases.commands.finish(conn, command, TerminalDisposition(status, receipt.model_dump_json().encode()))
            return receipt
        return self.requests.leases.commands.transact(transaction)

    @staticmethod
    def _origin(conn, params):
        row = conn.execute(text('SELECT canonical_frame FROM runtime.supervision_requests WHERE tenant_id=:tenant '
            'AND project_id=:project AND run_id=:run AND decision_id=:decision AND request_sha256=:request'), params).first()
        require(row is not None, 'supervision_request_unavailable')
        return RequestFrame.from_bytes(bytes(row[0]))

    def response(self, principal, response_id):
        principal.require('read')
        params = {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id, 'response': response_id}
        with self.requests.engine.connect() as conn:
            row = conn.execute(text(RESPONSES + ' AND s.response_id=:response'), params).mappings().one_or_none()
        return None if row is None else StoredResponse.from_row(row)

    def receipt(self, principal, command):
        principal.require('read', command.identity)
        checked = parse_supervision_command('runtime.supervision.respond', command.canonical_bytes)
        require(checked == command, 'response_command_mismatch')
        with self.requests.engine.connect() as conn:
            row = conn.execute(text('SELECT profile,request_sha256,canonical_bytes,status,receipt FROM runtime.commands '
                'WHERE ' + WHERE), _bindings(command)).mappings().one_or_none()
        if row is None:
            return None
        require(row['profile'] == command.profile and row['request_sha256'] == command.sha256 and
                bytes(row['canonical_bytes']) == command.canonical_bytes, 'response_command_mismatch')
        return None if row['status'] == 'pending' else SupervisionCommandReceipt.model_validate_json(json.dumps(row['receipt']))
