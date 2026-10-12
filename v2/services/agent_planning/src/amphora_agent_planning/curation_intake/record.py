"""Immutable original receipt projection and stored-index validation."""
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime

from amphora_contracts_campaign_curation import CurationReceipt, CurationRef, CurationView

from ..context.policy import require
from .commands import CurationCommand


def encoded(record):
    return (json.dumps(record.model_dump(mode='json'), sort_keys=True, separators=(',', ':'),
                       ensure_ascii=False, allow_nan=False) + '\n').encode()


@dataclass(frozen=True)
class OriginalCuration:
    incoming: CurationCommand
    recorded_at: datetime

    def __post_init__(self):
        require(isinstance(self.recorded_at, datetime) and self.recorded_at.utcoffset() is not None,
                'curation_recorded_time_required')
        object.__setattr__(self, 'recorded_at', self.recorded_at.astimezone(UTC))

    @property
    def receipt(self):
        command = self.incoming.command
        return CurationReceipt(identity=command.identity, request_sha256=command.sha256,
            reference=CurationRef(scope=command.identity.scope, curation_id=self.incoming.curation_id),
            revision=0, phase='queued', reason_code=None,
            created_at=self.recorded_at, updated_at=self.recorded_at)

    def view(self):
        return CurationView(receipt=self.receipt, specification=self.incoming.request.payload,
            provider=None, proposal=None, capability_requests=(), validated_draft=None)

    @classmethod
    def restore(cls, row):
        incoming = CurationCommand.restore(bytes(row['command_bytes']))
        command = incoming.command
        identity = command.identity
        require(identity.scope.tenant_id == row['tenant_id'] and identity.scope.project_id == row['project_id']
            and identity.actor_id == row['actor_id'] and identity.command_id == row['command_id']
            and incoming.curation_id == row['curation_id'] and command.sha256 == row['command_sha256']
            and command.canonical_bytes == bytes(row['command_bytes']), 'stored_curation_command_mismatch')
        record = cls(incoming, row['recorded_at'])
        receipt_bytes = bytes(row['receipt_bytes'])
        require(encoded(record.receipt) == receipt_bytes
                and hashlib.sha256(receipt_bytes).hexdigest() == row['receipt_sha256'],
                'stored_curation_receipt_mismatch')
        return record
