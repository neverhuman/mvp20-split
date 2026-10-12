"""Immutable authorized command and the exact original capability it addresses."""
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib

from amphora_contracts_campaign_curation import CapabilityFulfillmentReceipt, CapabilityRequestView

from ..capability_requests.projection import CapabilityAddress, OriginalCapability
from ..context.policy import require
from ..curation_intake.commands import FulfillmentCommand
from ..curation_intake.record import encoded


@dataclass(frozen=True)
class OriginalFulfillment:
    incoming: FulfillmentCommand
    capability: OriginalCapability
    recorded_at: datetime

    def __post_init__(self):
        require(self.incoming.request.payload.request == self.capability.reference,
                'fulfillment_original_request')
        require(isinstance(self.recorded_at, datetime) and self.recorded_at.utcoffset() is not None,
                'fulfillment_recorded_time_required')
        object.__setattr__(self, 'recorded_at', self.recorded_at.astimezone(UTC))

    @property
    def receipt(self):
        return CapabilityFulfillmentReceipt(identity=self.incoming.command.identity,
            request_sha256=self.incoming.command.sha256, specification=self.incoming.request.payload,
            status='pending', reason_code=None, created_at=self.recorded_at)

    def require_worker(self, principal):
        principal.require('execute_curations', self.incoming.command.identity.scope)
        if principal.actor_id != self.incoming.command.identity.actor_id:
            raise PermissionError('planning_access_denied')

    @classmethod
    def restore(cls, row):
        incoming = FulfillmentCommand.restore(bytes(row['command_bytes']))
        command, identity = incoming.command, incoming.command.identity
        require(identity.scope.tenant_id == row['tenant_id'] and identity.scope.project_id == row['project_id']
            and identity.actor_id == row['actor_id'] and identity.command_id == row['command_id']
            and incoming.fulfillment_id == row['fulfillment_id'] and command.sha256 == row['command_sha256']
            and command.canonical_bytes == bytes(row['command_bytes']), 'stored_fulfillment_command_mismatch')
        raw = bytes(row['capability_bytes'])
        view = CapabilityRequestView.model_validate_json(raw)
        address = CapabilityAddress.parse(view.reference.request_id)
        require(address is not None and view.status == 'requested' and view.fulfillment is None,
                'stored_fulfillment_capability_mismatch')
        capability = OriginalCapability(view.curation, view.proposal_sha256, address.ordinal, view.gap)
        require(capability.view() == view and encoded(view) == raw
            and hashlib.sha256(raw).hexdigest() == row['capability_sha256']
            and view.reference.request_id == row['request_id'], 'stored_fulfillment_capability_mismatch')
        original = cls(incoming, capability, row['recorded_at'])
        receipt = bytes(row['receipt_bytes'])
        require(receipt == encoded(original.receipt)
            and hashlib.sha256(receipt).hexdigest() == row['receipt_sha256'], 'stored_fulfillment_receipt_mismatch')
        return original
