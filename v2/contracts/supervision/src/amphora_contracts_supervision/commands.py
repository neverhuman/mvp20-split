"""Closed explicit numeric-v2 command families and separate recording receipts."""

import json
from typing import Annotated, Literal

from amphora_contracts_commands import (
    CanonicalCommand,
    CommandEncodingError,
    CommandIdentity,
)
from amphora_contracts_core import Digest, Identifier, SafePositiveInt, WireModel
from pydantic import Field

from .requests import SupervisionRequest
from .responses import CancelSupervision, SupervisionResponse


class SupervisionReceiptBinding(WireModel):
    identity: CommandIdentity
    request_sha256: Digest
    operation_id: Identifier


class SupervisionCommit(WireModel):
    kind: Literal['request', 'response', 'cancellation', 'decision']
    object_id: Identifier
    revision: SafePositiveInt
    content_sha256: Digest


class SupervisionPending(WireModel):
    status: Literal['pending']
    binding: SupervisionReceiptBinding


class SupervisionRejected(WireModel):
    status: Literal['rejected']
    binding: SupervisionReceiptBinding
    reason_code: Identifier


class SupervisionRecorded(WireModel):
    status: Literal['recorded']
    binding: SupervisionReceiptBinding
    committed: SupervisionCommit


class SupervisionCommandReceipt(WireModel):
    schema_version: Literal['1'] = '1'
    outcome: Annotated[SupervisionPending | SupervisionRejected | SupervisionRecorded, Field(discriminator='status')]


def parse_supervision_command(family, raw):
    try:
        model = {'planning.supervision.request': SupervisionRequest,
                 'runtime.supervision.respond': SupervisionResponse,
                 'runtime.supervision.cancel': CancelSupervision}[family]
    except KeyError as error:
        raise CommandEncodingError('unknown_family') from error
    command = CanonicalCommand.for_family(raw, family, model, allow_numeric=True)
    if command.profile != 'amphora-command-v2':
        raise CommandEncodingError('invalid_encoding')
    payload = json.loads(command.canonical_bytes)['payload']
    if payload['reference']['scope'] != command.identity.scope.model_dump(mode='json'):
        raise CommandEncodingError('scope_mismatch')
    if family == 'planning.supervision.request' and payload['planning_request']['actor_id'] != command.identity.actor_id:
        raise CommandEncodingError('actor_mismatch')
    return command
