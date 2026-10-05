"""Atomic original request/outgoing intent; no peer I/O or accepted decision."""

import json
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType

from amphora_contracts_supervision import parse_supervision_command
from sqlalchemy import text

from ..lifecycle.claims import RuntimeLeases
from ..supervision_requests.binding import encoded
from ..supervision_scope.observations import require
from .current import verify_current
from .frames import RequestFrame
from .series import RequestSeries

SELECT = '''SELECT r.*,o.canonical_command,o.command_sha256,o.created_at AS intent_created_at,
 o.actor_id AS command_actor,o.command_id,o.profile,o.family FROM runtime.supervision_requests r
 JOIN runtime.supervision_outbox o USING(tenant_id,project_id,run_id,decision_id,request_sha256)
 WHERE r.tenant_id=:tenant AND r.project_id=:project AND r.run_id=:run AND r.decision_id=:decision'''


def outgoing(frame, canonical):
    command = parse_supervision_command('planning.supervision.request', canonical)
    require(command.canonical_bytes == canonical, 'noncanonical_outgoing_command')
    require(len(canonical) <= 524288, 'outgoing_command_size')
    require(encoded(frame.request) == encoded(type(frame.request).model_validate_json(
        json.dumps(json.loads(canonical)['payload']))), 'outgoing_request_mismatch')
    return command


@dataclass(frozen=True)
class StoredRequest:
    frame: RequestFrame
    canonical_command: bytes
    created_at: datetime
    intent_created_at: datetime

    @classmethod
    def from_row(cls, row):
        frame = RequestFrame.from_bytes(bytes(row['canonical_frame']))
        request = frame.request
        command = outgoing(frame, bytes(row['canonical_command']))
        expected = {'tenant_id': request.reference.scope.tenant_id,
            'project_id': request.reference.scope.project_id, 'run_id': request.reference.run_id,
            'decision_id': request.reference.decision_id, 'ordinal': request.lineage.ordinal,
            'plan_sha256': request.snapshot.cut.plan_sha256, 'prepared_by': frame.document().prepared_by,
            'planning_actor': request.planning_request.actor_id,
            'engagement_id': request.planning_request.reference.engagement_id,
            'checkpoint_id': request.checkpoint_id, 'request_sha256': frame.request_sha256,
            'frame_sha256': frame.sha256, 'root_request_sha256': request.lineage.root_request_sha256,
            'parent_request_sha256': request.lineage.parent_request_sha256,
            'command_actor': command.identity.actor_id, 'command_id': command.identity.command_id,
            'family': command.identity.command_family, 'profile': command.profile, 'command_sha256': command.sha256}
        require(all(row[key] == value for key, value in expected.items()), 'stored_origin_mismatch')
        return cls(frame, command.canonical_bytes, row['created_at'], row['intent_created_at'])


class RequestJournal:
    def __init__(self, engine, planning_actors):
        self.engine = engine
        self.leases = RuntimeLeases(engine)
        # Operator configuration: (tenant, project, Runtime preparer) -> Planning actor.
        self.planning_actors = MappingProxyType(dict(planning_actors))

    @staticmethod
    def params(principal, run_id, decision_id):
        return {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id,
                'run': run_id, 'decision': decision_id}

    def series(self, principal, run_id, decision_id):
        principal.require('read')
        with self.engine.connect() as conn:
            rows = conn.execute(text(SELECT + ' ORDER BY r.ordinal'),
                                self.params(principal, run_id, decision_id)).mappings().all()
        result = tuple(StoredRequest.from_row(row) for row in rows)
        if result:
            RequestSeries(tuple(item.frame for item in result))
        return result

    def prepare(self, principal, frame, canonical_command):
        principal.require('supervise_prepare')
        frame = RequestFrame.from_bytes(frame.canonical)
        request = frame.request
        require(request.reference.scope == principal.scope and
                frame.document().prepared_by == principal.actor_id, 'preparer_scope_mismatch')
        key = (principal.scope.tenant_id, principal.scope.project_id, principal.actor_id)
        require(self.planning_actors.get(key) == request.planning_request.actor_id, 'planning_delegation_unavailable')
        command = outgoing(frame, canonical_command)
        params = self.params(principal, request.reference.run_id, request.reference.decision_id)

        def transaction(conn):
            run = self.leases._run(conn, params)
            rows = conn.execute(text(SELECT + ' ORDER BY r.ordinal'), params).mappings().all()
            previous = tuple(StoredRequest.from_row(row) for row in rows)
            ordinal = request.lineage.ordinal
            if ordinal <= len(previous):
                original = previous[ordinal - 1]
                require(original.frame.canonical == frame.canonical and
                        original.canonical_command == command.canonical_bytes, 'request_identity_conflict')
                return original
            RequestSeries((*tuple(item.frame for item in previous), frame))
            verify_current(conn, params, run, frame)
            values = {**params, 'ordinal': ordinal, 'plan': request.snapshot.cut.plan_sha256,
                'preparer': principal.actor_id, 'actor': request.planning_request.actor_id,
                'engagement': request.planning_request.reference.engagement_id,
                'checkpoint': request.checkpoint_id, 'request': frame.request_sha256,
                'frame_hash': frame.sha256, 'root': request.lineage.root_request_sha256,
                'parent': request.lineage.parent_request_sha256, 'frame': frame.canonical,
                'command': command.identity.command_id, 'profile': command.profile,
                'command_hash': command.sha256, 'bytes': command.canonical_bytes}
            conn.execute(text('''INSERT INTO runtime.supervision_requests
                (tenant_id,project_id,run_id,decision_id,ordinal,plan_sha256,prepared_by,planning_actor,
                 engagement_id,checkpoint_id,request_sha256,frame_sha256,root_request_sha256,
                 parent_request_sha256,canonical_frame) VALUES
                (:tenant,:project,:run,:decision,:ordinal,:plan,:preparer,:actor,:engagement,:checkpoint,
                 :request,:frame_hash,:root,:parent,:frame)'''), values)
            conn.execute(text('''INSERT INTO runtime.supervision_outbox
                (tenant_id,project_id,run_id,decision_id,request_sha256,actor_id,family,command_id,
                 profile,command_sha256,canonical_command) VALUES
                (:tenant,:project,:run,:decision,:request,:actor,'planning.supervision.request',:command,
                 :profile,:command_hash,:bytes)'''), values)
            row = conn.execute(text(SELECT + ' AND r.ordinal=:ordinal'), values).mappings().one()
            return StoredRequest.from_row(row)

        return self.leases.commands.transact(transaction)
