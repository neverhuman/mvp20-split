"""Public literal commands and independently constructed expected recording receipts."""

import hashlib
import json
from pathlib import Path

from amphora_contracts_supervision import (
    CancelSupervision,
    SupervisionCommandReceipt,
    SupervisionResponse,
    parse_supervision_command,
)

FIXTURES = Path(__file__).absolute().parents[4] / 'contracts/supervision/tests/fixtures'


def command_and_payload(family='runtime.supervision.respond'):
    file, model = ('response-command.json', SupervisionResponse) if family == 'runtime.supervision.respond' else ('cancel-command.json', CancelSupervision)
    command = parse_supervision_command(family, (FIXTURES / file).read_bytes())
    return command, model.model_validate_json(json.dumps(json.loads(command.canonical_bytes)['payload']))


def receipt(command, payload, status='recorded'):
    binding = {'identity': command.identity.model_dump(mode='json'), 'request_sha256': command.sha256,
               'operation_id': 'owner-operation-1'}
    outcome = {'status': status, 'binding': binding}
    if status == 'recorded':
        kind, key = ('response', payload.response_id) if isinstance(payload, SupervisionResponse) else ('cancellation', payload.cancellation_id)
        raw = json.dumps(payload.model_dump(mode='json'), sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
        outcome['committed'] = {'kind': kind, 'object_id': key, 'revision': 1, 'content_sha256': hashlib.sha256(raw).hexdigest()}
    elif status == 'rejected':
        outcome['reason_code'] = 'owner_rejected'
    return SupervisionCommandReceipt.model_validate_json(json.dumps({'outcome': outcome}))
