"""Durable heartbeat delivery policy; observations never reserve execution work."""

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from ..profile import fields, label, require


@dataclass(frozen=True)
class ReplicaBinding:
    """Local profile deliberately uses the narrower deployment identifier vocabulary."""

    installation_id: str
    tenant_id: str
    project_id: str
    worker_id: str
    deployment_id: str
    replica_id: str

    def __post_init__(self):
        for value in asdict(self).values():
            label(value, 'heartbeat_binding')

    @property
    def scope(self):
        return {'tenant_id': self.tenant_id, 'project_id': self.project_id}

    def command(self, revision, free_slots):
        return {'identity': {'schema_version': '1', 'scope': self.scope,
            'actor_id': self.worker_id, 'command_family': 'registry.heartbeat',
            'command_id': uuid.uuid4().hex}, 'payload': {
            'deployment_id': self.deployment_id, 'replica_id': self.replica_id,
            'expected_revision': revision, 'free_slots': free_slots, 'ttl_seconds': 15}}


class HeartbeatJournal:
    """One stable logical replica; caller holds writer lease and serializes calls.

    Persist intent before delivery. Never replace an uncertain positive request with
    a zero request: the unknown Registry revision must first be reconciled. Positive
    retries require fresh readiness, including after process restart. Otherwise the
    unresolved observation is exposed and any existing server lease must expire.
    """

    def __init__(self, path, binding):
        self.path = Path(path)
        self.binding = binding

    def read(self):
        if not self.path.exists():
            return {'profile': 'local-heartbeat-v1', 'binding': asdict(self.binding),
                    'revision': 0, 'pending': None}
        with self.path.open('rb') as stream:
            raw = stream.read(8193)
        require(len(raw) <= 8192, 'heartbeat_journal_size')
        record = fields(json.loads(raw), 'profile binding revision pending', 'heartbeat_journal')
        require(record['profile'] == 'local-heartbeat-v1' and record['binding'] == asdict(self.binding),
                'heartbeat_journal_binding')
        revision = record['revision']
        require(type(revision) is int and 0 <= revision <= 2**53 - 1, 'heartbeat_revision')
        pending = record['pending']
        if pending is not None:
            fields(pending, 'identity payload', 'heartbeat_pending')
            identity = fields(pending['identity'], 'schema_version scope actor_id command_family command_id',
                              'heartbeat_identity')
            label(identity['command_id'], 'heartbeat_command_id')
            expected = self.binding.command(revision, 0)
            expected['identity']['command_id'] = identity['command_id']
            slots = pending['payload'].get('free_slots') if type(pending['payload']) is dict else None
            require(type(slots) is int and slots in (0, 1), 'heartbeat_slots')
            require(all(type(pending['payload'].get(key)) is int for key in
                        ('expected_revision', 'ttl_seconds')), 'heartbeat_pending_numbers')
            expected['payload']['free_slots'] = slots
            require(pending == expected, 'heartbeat_pending_binding')
        return record

    def _write(self, record):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name('.heartbeat-' + uuid.uuid4().hex + '.tmp')
        try:
            with temporary.open('xb') as stream:
                stream.write(json.dumps(record, sort_keys=True, separators=(',', ':')).encode())
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def prepare(self, *, ready):
        require(type(ready) is bool, 'heartbeat_readiness')
        record = self.read()
        pending = record['pending']
        if pending is not None:
            if pending['payload']['free_slots'] and not ready:
                return None  # Explicit uncertainty, never a successful withdrawal.
            return pending
        require(record['revision'] < 2**53 - 1, 'heartbeat_revision_exhausted')
        pending = self.binding.command(record['revision'], int(ready))
        self._write(dict(record, pending=pending))
        return pending

    def accept(self, receipt):
        """Only an exact accepted observation advances revision; all else retains intent."""
        record = self.read()
        pending = record['pending']
        require(pending is not None, 'heartbeat_no_pending')
        fields(receipt, 'schema_version operation_id status reason_code release deployment heartbeat decision',
               'heartbeat_receipt')
        label(receipt['operation_id'], 'heartbeat_operation_id')
        require(receipt['schema_version'] == '1' and receipt['status'] == 'accepted'
                and receipt['reason_code'] == 'observed'
                and all(receipt[key] is None for key in ('release', 'deployment', 'decision')),
                'heartbeat_not_accepted')
        snapshot = fields(receipt['heartbeat'],
            'scope deployment_id replica_id worker_id revision free_slots observed_at expires_at', 'heartbeat_snapshot')
        payload = pending['payload']
        require(snapshot['scope'] == self.binding.scope and snapshot['deployment_id'] == self.binding.deployment_id
                and snapshot['replica_id'] == self.binding.replica_id and snapshot['worker_id'] == self.binding.worker_id
                and type(snapshot['revision']) is int and snapshot['revision'] == record['revision'] + 1
                and type(snapshot['free_slots']) is int and snapshot['free_slots'] == payload['free_slots'],
                'heartbeat_receipt_binding')
        try:
            observed = datetime.fromisoformat(snapshot['observed_at'])
            expires = datetime.fromisoformat(snapshot['expires_at'])
            valid = observed.utcoffset() is not None and expires.utcoffset() is not None and (
                expires - observed).total_seconds() == payload['ttl_seconds']
        except (ValueError, TypeError):
            valid = False
        require(valid, 'heartbeat_receipt_time')
        self._write(dict(record, revision=snapshot['revision'], pending=None))
        # This historical receipt may already be expired. Never synthesize local freshness.
        return {'revision': snapshot['revision'], 'free_slots': snapshot['free_slots'],
                'observed_at': snapshot['observed_at'], 'expires_at': snapshot['expires_at']}
