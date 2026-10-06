"""Measured primary results never adopt a more favorable late response."""

import hashlib
from dataclasses import dataclass

from ..context.policy import require
from ..evaluation.protocol import canonical
from ..evaluation.records import ObservationRecord


@dataclass(frozen=True)
class MeasuredObservation:
    observation: ObservationRecord
    request_sha256: str
    source_sha256: str

    @classmethod
    def from_attempt(cls, protocol, task, attempt):
        require(attempt.binding == task.binding and attempt.observation is not None, 'evaluation_attempt_binding')
        observed = attempt.observation
        wire = observed.document()
        status = {'abstained': 'scientific_abstention', 'unavailable': 'provider_error',
                  'policy_rejected': 'rejected'}.get(wire.status, wire.status)
        payload = None
        if status == 'proposed':
            payload = observed.capture.content.decode('utf-8')
        elif status == 'rejected':
            payload = canonical({'status': wire.status, 'reason_code': wire.reason_code}).decode()
        result = ObservationRecord(protocol_sha256=protocol.sha256, case_id=task.case_id,
            repetition=task.repetition, status=status, payload_json=payload)
        return cls(result, task.request.sha256, hashlib.sha256(observed.canonical).hexdigest())
