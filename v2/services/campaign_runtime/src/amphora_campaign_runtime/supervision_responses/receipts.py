"""Recording a response is distinct from a Runtime decision winner/effect."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_supervision import (
    CancelSupervision,
    CheckpointRequest,
    SupervisionCommandReceipt,
    SupervisionRequest,
    SupervisionResponse,
    parse_supervision_command,
)

from ..supervision_requests.binding import encoded
from ..supervision_requests.profiles import request_command
from ..supervision_scope.observations import require


@dataclass(frozen=True)
class SupervisionReceiptObservation:
    canonical: bytes
    readback_canonical: bytes | None

    @classmethod
    def observe(cls, command, receipt, *, readback=None, previous=None):
        family = command.identity.command_family
        checked = (request_command(family, command.canonical_bytes) if family == 'planning.supervision.request.v2'
                   else parse_supervision_command(family, command.canonical_bytes))
        require(checked == command, 'command_binding_mismatch')
        record = SupervisionCommandReceipt.model_validate_json(receipt.model_dump_json())
        binding = record.outcome.binding
        require(binding.identity == command.identity and binding.request_sha256 == command.sha256,
                'receipt_command_mismatch')
        if previous is not None:
            old = previous.document()
            require(old.outcome.binding == binding, 'receipt_operation_changed')
            require(previous.readback_canonical is None or old.outcome.status == 'recorded',
                    'unexpected_previous_readback')
            if old.outcome.status != 'pending':
                require(old == record, 'terminal_receipt_changed')
        raw = None
        if record.outcome.status == 'recorded':
            model, kind, identity_field = {
                'planning.supervision.request': (SupervisionRequest, 'request', None),
                'planning.supervision.request.v2': (CheckpointRequest, 'request', None),
                'runtime.supervision.respond': (SupervisionResponse, 'response', 'response_id'),
                'runtime.supervision.cancel': (CancelSupervision, 'cancellation', 'cancellation_id'),
            }[family]
            payload = model.model_validate_json(json.dumps(json.loads(command.canonical_bytes)['payload']))
            committed = record.outcome.committed
            identity = (payload.planning_request.reference.engagement_id if identity_field is None
                        else getattr(payload, identity_field))
            expected = encoded(payload)
            require(committed.kind == kind and committed.object_id == identity and committed.revision == 1 and
                    committed.content_sha256 == hashlib.sha256(expected).hexdigest(), 'receipt_commit_mismatch')
            if readback is not None:
                actual = model.model_validate_json(readback.model_dump_json())
                require(actual == payload, 'receipt_readback_mismatch')
                raw = encoded(actual)
            elif previous is not None and previous.readback_canonical is not None:
                actual = model.model_validate_json(previous.readback_canonical)
                require(actual == payload and previous.readback_canonical == expected, 'receipt_readback_mismatch')
                raw = expected
        else:
            require(readback is None, 'unexpected_receipt_readback')
        return cls(encoded(record), raw)

    def document(self):
        return SupervisionCommandReceipt.model_validate_json(self.canonical)

    @property
    def status(self):
        status = self.document().outcome.status
        return 'awaiting_readback' if status == 'recorded' and self.readback_canonical is None else status
