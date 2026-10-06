"""One durable exchange phase per tick, with original receipt recovery first."""

from uuid import uuid4

from ..supervision_client import (
    ExchangeAbsent,
    ExchangeConflict,
    ExchangeDenied,
    ExchangeInvalid,
    ExchangeUnavailable,
    ExchangeWindow,
)
from ..supervision_scope.observations import require
from .progress import DeliveryProgress

FAILURES = {
    ExchangeAbsent: 'delivery_readback_absent',
    ExchangeConflict: 'delivery_peer_conflict',
    ExchangeDenied: 'delivery_peer_denied',
    ExchangeInvalid: 'delivery_peer_rejected',
    ExchangeUnavailable: 'delivery_peer_uncertain',
}


class RequestDispatcher:
    def __init__(self, journal, client):
        self.journal, self.client = journal, client

    def run(self, principal, reference, request_sha256):
        progress = DeliveryProgress.load(self.journal, principal, reference, request_sha256)
        if progress.terminal:
            return progress
        command = progress.command
        require(self.client is not None and self.client.actor_id == command.identity.actor_id and
                self.client.scope == command.identity.scope and self.client.family == command.identity.command_family,
                'delivery_client_authority')
        lease = self.journal.claim(principal, reference, request_sha256, event_id=uuid4().hex)
        if lease is None:
            return DeliveryProgress.load(self.journal, principal, reference, request_sha256)
        # Another worker may have recorded a receipt between the first read and our claim.
        progress = DeliveryProgress.load(self.journal, principal, reference, request_sha256)
        previous, window = progress.previous, ExchangeWindow()
        try:
            if previous is not None and previous.status == 'awaiting_readback':
                observed = self.client.readback(command, previous, window)
            else:
                try:
                    observed = self.client.receipt(command, window, previous=previous)
                except ExchangeAbsent:
                    if previous is not None:
                        raise ExchangeUnavailable('delivery_receipt_disappeared') from None
                    observed = self.client.submit(command, window,
                        guard=lambda: self.journal.guard(principal, lease))
        except tuple(FAILURES) as error:
            # Retain a closed reason, never peer bodies, credentials or arbitrary exception text.
            self.journal.observe(principal, lease, event_id=uuid4().hex, reason=FAILURES[type(error)])
        else:
            request_type = type(progress.original.frame.request)
            readback = None if observed.readback_canonical is None else request_type.model_validate_json(
                observed.readback_canonical)
            self.journal.observe(principal, lease, event_id=uuid4().hex, receipt=observed.document(), readback=readback)
        return DeliveryProgress.load(self.journal, principal, reference, request_sha256)
