"""Projection of owned original command and append-only delivery evidence."""

from dataclasses import dataclass

from ..supervision_journal.delivery import TERMINAL
from ..supervision_journal.delivery_values import DeliveryEvent
from ..supervision_journal.storage import StoredRequest, outgoing
from ..supervision_requests.binding import encoded
from ..supervision_responses import SupervisionReceiptObservation
from ..supervision_scope.observations import require


@dataclass(frozen=True)
class DeliveryProgress:
    original: StoredRequest
    events: tuple[DeliveryEvent, ...]

    @classmethod
    def load(cls, journal, principal, reference, request_sha256):
        require(principal.scope == reference.scope, 'delivery_scope_mismatch')
        series = journal.requests.series(principal, reference.run_id, reference.decision_id)
        original = next((item for item in series if item.frame.request_sha256 == request_sha256), None)
        require(original is not None, 'supervision_request_unavailable')
        return cls(original, journal.history(principal, reference, request_sha256))

    @property
    def command(self):
        return outgoing(self.original.frame, self.original.canonical_command)

    @property
    def terminal(self):
        return bool(self.events and self.events[-1].kind in TERMINAL)

    @property
    def previous(self):
        for event in reversed(self.events):
            evidence = event.evidence
            if evidence.receipt is not None:
                return SupervisionReceiptObservation(encoded(evidence.receipt),
                    None if evidence.readback is None else encoded(evidence.readback))
        return None
