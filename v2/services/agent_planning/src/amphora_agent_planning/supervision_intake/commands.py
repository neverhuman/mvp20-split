"""Exact incoming identity and recorded receipt projection, without provider grants."""

import json
from dataclasses import dataclass

from amphora_contracts_supervision import (
    SupervisionCommandReceipt,
    parse_checkpoint_command,
    parse_supervision_command,
)

from ..context.policy import require
from .snapshot import CheckpointIntakeSnapshot, IntakeSnapshot, encoded


def request_command(family, raw):
    require(family in {'planning.supervision.request', 'planning.supervision.request.v2'},
            'supervision_request_family')
    return (parse_checkpoint_command(raw) if family.endswith('.v2')
            else parse_supervision_command(family, raw))


@dataclass(frozen=True)
class IncomingRequest:
    command: object
    snapshot: IntakeSnapshot

    @classmethod
    def bind(cls, principal, command):
        checked = request_command(command.identity.command_family, command.canonical_bytes)
        require(checked == command, 'supervision_command_binding_mismatch')
        require(command.identity.actor_id == principal.actor_id and command.identity.scope == principal.scope,
                'supervision_actor_mismatch')
        model = CheckpointIntakeSnapshot if command.identity.command_family.endswith('.v2') else IntakeSnapshot
        request = model.record_type.model_validate_json(json.dumps(json.loads(command.canonical_bytes)['payload']))
        return cls(command, model.bind(request, principal))

    @property
    def params(self):
        identity = self.command.identity
        return {'tenant': identity.scope.tenant_id, 'project': identity.scope.project_id,
                'actor': identity.actor_id, 'family': identity.command_family, 'command': identity.command_id}

    def receipt(self, operation_id, reason=None):
        outcome = {'status': 'rejected' if reason else 'recorded', 'binding': {
            'identity': self.command.identity.model_dump(mode='json'),
            'request_sha256': self.command.sha256, 'operation_id': operation_id}}
        if reason:
            outcome['reason_code'] = reason
        else:
            request = self.snapshot.document()
            outcome['committed'] = {'kind': 'request', 'object_id': request.planning_request.reference.engagement_id,
                'revision': 1, 'content_sha256': self.snapshot.sha256}
        return SupervisionCommandReceipt.model_validate_json(json.dumps({'outcome': outcome}))


def stored_receipt(row, principal):
    command = request_command(row['family'], bytes(row['canonical_command']))
    incoming = IncomingRequest.bind(principal, command)
    require(command.profile == row['profile'] and command.sha256 == row['command_sha256'] and
            command.canonical_bytes == bytes(row['canonical_command']) and
            command.identity.command_id == row['command_id'] and command.identity.command_family == row['family'],
            'stored_supervision_command_mismatch')
    receipt = SupervisionCommandReceipt.model_validate_json(bytes(row['canonical_receipt']))
    reason = receipt.outcome.reason_code if receipt.outcome.status == 'rejected' else None
    require(reason is None or reason in {'planning_request_conflict', 'supervision_request_conflict'},
            'stored_supervision_rejection_mismatch')
    require(receipt == incoming.receipt(row['operation_id'], reason) and
            encoded(receipt) == bytes(row['canonical_receipt']), 'stored_supervision_receipt_mismatch')
    expected = incoming.snapshot.document().planning_request.reference.engagement_id if reason is None else None
    require(row['committed_engagement_id'] == expected, 'stored_supervision_commit_mismatch')
    return incoming, receipt
