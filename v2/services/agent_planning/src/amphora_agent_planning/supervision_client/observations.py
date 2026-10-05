"""Recording a response is distinct from a Runtime decision winner/effect."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_supervision import (
    CancelSupervision,
    SupervisionCommandReceipt,
    SupervisionResponse,
    parse_supervision_command,
)

from ..context.policy import require
from ..supervision_intake.snapshot import encoded


@dataclass(frozen=True)
class RecordingObservation:
    canonical: bytes
    readback_canonical: bytes | None

    @classmethod
    def observe(cls, command, receipt, *, readback=None, previous=None):
        family = command.identity.command_family
        require(family in {"runtime.supervision.respond", "runtime.supervision.cancel"}, "supervisor_runtime_family")
        checked = parse_supervision_command(family, command.canonical_bytes)
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
                'runtime.supervision.respond': (SupervisionResponse, 'response', 'response_id'),
                'runtime.supervision.cancel': (CancelSupervision, 'cancellation', 'cancellation_id'),
            }[family]
            payload = model.model_validate_json(json.dumps(json.loads(command.canonical_bytes)['payload']))
            committed = record.outcome.committed
            identity = getattr(payload, identity_field)
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
