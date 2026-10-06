"""Atomic Planning-owned wrapper, original request and command receipt; no calls."""

import json
import uuid

from sqlalchemy import text

from ..context.policy import require
from ..persistence.journal import KEY, PlanningJournal
from .commands import IncomingRequest, stored_receipt
from .snapshot import encoded, read_snapshot

COMMAND_KEY = 'tenant_id=:tenant AND project_id=:project AND actor_id=:actor AND family=:family AND command_id=:command'


class SupervisionIntake:
    def __init__(self, engine):
        self.engine = engine
        self.requests = PlanningJournal(engine)

    @staticmethod
    def _wrapper(conn, key, principal):
        row = conn.execute(text('SELECT * FROM planning.supervision_requests WHERE ' + KEY), key).mappings().one_or_none()
        if row is None:
            return None
        snapshot = read_snapshot(bytes(row['canonical_request']), principal)
        request = snapshot.document()
        require(row['actor_id'] == principal.actor_id and row['request_sha256'] == snapshot.sha256 and
                row['planning_request_sha256'] == snapshot.planning.sha256 and
                row['engagement_id'] == request.planning_request.reference.engagement_id and
                row['run_id'] == request.reference.run_id and row['decision_id'] == request.reference.decision_id and
                row['ordinal'] == request.lineage.ordinal, 'stored_supervision_request_mismatch')
        original = PlanningJournal._request(conn, key, principal)
        require(original is not None and original.canonical == snapshot.planning.canonical, 'stored_planning_request_mismatch')
        return snapshot

    def receive(self, principal, command):
        principal.require('record_requests', command.identity.scope)
        incoming = IncomingRequest.bind(principal, command)
        request = incoming.snapshot.document()
        key = {**incoming.params, 'engagement': request.planning_request.reference.engagement_id}
        with self.engine.begin() as conn:
            token = json.dumps(['planning.supervision.command.v1', key['tenant'], key['project'],
                                key['actor'], key['family'], key['command']])
            conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:token,0))'), {'token': token})
            row = conn.execute(text('SELECT * FROM planning.supervision_commands WHERE ' + COMMAND_KEY), key).mappings().one_or_none()
            if row is not None:
                original, receipt = stored_receipt(row, principal)
                require(original.command == command, 'supervision_command_conflict')
                return receipt
            slot = json.dumps(['planning.supervision.slot.v1', key['tenant'], key['project'],
                               request.reference.run_id, request.reference.decision_id])
            conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:token,0))'), {'token': slot})
            self.requests._lock(conn, key)
            previous = self.requests._request(conn, key, principal)
            wrapper = self._wrapper(conn, key, principal)
            occupied = conn.execute(text('SELECT engagement_id FROM planning.supervision_requests WHERE tenant_id=:tenant '
                'AND project_id=:project AND run_id=:run AND decision_id=:decision AND ordinal=:ordinal'),
                {**key, 'run': request.reference.run_id, 'decision': request.reference.decision_id,
                 'ordinal': request.lineage.ordinal}).scalar_one_or_none()
            reason = None
            if previous is not None and previous.canonical != incoming.snapshot.planning.canonical:
                reason = 'planning_request_conflict'
            elif wrapper is not None and wrapper.canonical != incoming.snapshot.canonical or (
                    occupied is not None and occupied != key['engagement']):
                reason = 'supervision_request_conflict'
            if reason is None:
                if previous is None:
                    conn.execute(text('INSERT INTO planning.requests '
                        '(tenant_id,project_id,engagement_id,actor_id,request_sha256,canonical_bytes) '
                        'VALUES (:tenant,:project,:engagement,:actor,:digest,:canonical)'),
                        {**key, 'digest': incoming.snapshot.planning.sha256, 'canonical': incoming.snapshot.planning.canonical})
                if wrapper is None:
                    conn.execute(text('INSERT INTO planning.supervision_requests '
                        '(tenant_id,project_id,engagement_id,actor_id,run_id,decision_id,ordinal,planning_request_sha256,'
                        'request_sha256,canonical_request) VALUES '
                        '(:tenant,:project,:engagement,:actor,:run,:decision,:ordinal,:planning,:digest,:canonical)'),
                        {**key, 'run': request.reference.run_id, 'decision': request.reference.decision_id,
                         'ordinal': request.lineage.ordinal, 'planning': incoming.snapshot.planning.sha256,
                         'digest': incoming.snapshot.sha256, 'canonical': incoming.snapshot.canonical})
            receipt = incoming.receipt(uuid.uuid4().hex, reason)
            self._record_command(conn, key, incoming, receipt)
            return receipt

    @staticmethod
    def _record_command(conn, key, incoming, receipt):
        conn.execute(text('INSERT INTO planning.supervision_commands '
            '(tenant_id,project_id,actor_id,family,command_id,operation_id,profile,command_sha256,'
            'canonical_command,canonical_receipt,committed_engagement_id) VALUES '
            '(:tenant,:project,:actor,:family,:command,:operation,:profile,:digest,:canonical,:receipt,:committed)'),
            {**key, 'operation': receipt.outcome.binding.operation_id, 'profile': incoming.command.profile,
             'digest': incoming.command.sha256, 'canonical': incoming.command.canonical_bytes,
             'receipt': encoded(receipt), 'committed': key['engagement'] if receipt.outcome.status == 'recorded' else None})

    def request(self, principal, engagement_id):
        principal.require('read_attempts', principal.scope)
        key = {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id, 'engagement': engagement_id}
        with self.engine.connect() as conn:
            return self._wrapper(conn, key, principal)

    def receipt(self, principal, command_id, *, family='planning.supervision.request'):
        principal.require('read_attempts', principal.scope)
        require(family in {'planning.supervision.request', 'planning.supervision.request.v2'},
                'supervision_request_family')
        key = {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id, 'actor': principal.actor_id,
               'family': family, 'command': command_id}
        with self.engine.connect() as conn:
            row = conn.execute(text('SELECT * FROM planning.supervision_commands WHERE ' + COMMAND_KEY), key).mappings().one_or_none()
        return None if row is None else stored_receipt(row, principal)[1]
