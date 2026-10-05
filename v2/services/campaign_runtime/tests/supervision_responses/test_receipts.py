"""Command acknowledgment/readback retains identity without implying acceptance."""

import hashlib
import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_campaign_runtime.supervision_responses import SupervisionReceiptObservation
from amphora_contracts_supervision import (
    CancelSupervision,
    SupervisionCommandReceipt,
    parse_supervision_command,
)

from .support import origin, response


def command_and_payload(family):
    original, _ = origin()
    request = original.document()
    reply, _ = response()
    payload = {'planning.supervision.request': request, 'runtime.supervision.respond': reply,
        'runtime.supervision.cancel': CancelSupervision(cancellation_id='cancel-1', reference=request.reference,
            request_sha256=original.sha256, reason_code='declared_deadline')}[family]
    raw = {'encoding': 'amphora-command-v2', 'identity': {'schema_version': '1', 'command_family': family,
        'command_id': 'command-1', 'scope': request.reference.scope.model_dump(mode='json'),
        'actor_id': request.planning_request.actor_id}, 'payload': payload.model_dump(mode='json')}
    return parse_supervision_command(family, json.dumps(raw)), payload


def receipt(command, payload, status='recorded'):
    binding = {'identity': command.identity.model_dump(mode='json'), 'request_sha256': command.sha256,
               'operation_id': 'owner-operation-1'}
    outcome = {'status': status, 'binding': binding}
    if status == 'recorded':
        kind, identity = {'planning.supervision.request': ('request', lambda p: p.planning_request.reference.engagement_id),
                          'runtime.supervision.respond': ('response', lambda p: p.response_id),
                          'runtime.supervision.cancel': ('cancellation', lambda p: p.cancellation_id)}[command.identity.command_family]
        outcome['committed'] = {'kind': kind, 'object_id': identity(payload), 'revision': 1,
                                'content_sha256': hashlib.sha256(encoded(payload)).hexdigest()}
    elif status == 'rejected':
        outcome['reason_code'] = 'owner_rejected'
    return SupervisionCommandReceipt.model_validate_json(json.dumps({'outcome': outcome}))


@pytest.mark.parametrize('family', ['planning.supervision.request', 'runtime.supervision.respond',
                                    'runtime.supervision.cancel'])
def test_pending_to_recorded_requires_exact_readback_and_keeps_original_operation(family):
    command, payload = command_and_payload(family)
    pending = SupervisionReceiptObservation.observe(command, receipt(command, payload, 'pending'))
    assert pending.status == 'pending'
    accepted = receipt(command, payload)
    waiting = SupervisionReceiptObservation.observe(command, accepted, previous=pending)
    assert waiting.status == 'awaiting_readback'
    verified = SupervisionReceiptObservation.observe(command, accepted, readback=payload, previous=waiting)
    assert verified.status == 'recorded' and verified.readback_canonical == encoded(payload)
    assert SupervisionReceiptObservation.observe(command, accepted, readback=payload, previous=verified) == verified
    assert SupervisionReceiptObservation.observe(command, accepted, previous=verified) == verified
    assert verified.document().outcome.status == 'recorded'


@pytest.mark.parametrize('path,value,reason', [
    (('outcome', 'binding', 'request_sha256'), 'f' * 64, 'receipt_command_mismatch'),
    (('outcome', 'binding', 'identity', 'actor_id'), 'other', 'receipt_command_mismatch'),
    (('outcome', 'committed', 'kind'), 'decision', 'receipt_commit_mismatch'),
    (('outcome', 'committed', 'object_id'), 'other', 'receipt_commit_mismatch'),
    (('outcome', 'committed', 'revision'), 2, 'receipt_commit_mismatch'),
    (('outcome', 'committed', 'content_sha256'), 'f' * 64, 'receipt_commit_mismatch'),
])
def test_complete_commit_binding_not_only_status_is_verified(path, value, reason):
    command, payload = command_and_payload('runtime.supervision.respond')
    record = receipt(command, payload).model_dump(mode='json')
    target = record
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValueError, match=reason):
        SupervisionReceiptObservation.observe(command, SupervisionCommandReceipt.model_validate_json(json.dumps(record)))


def test_recorded_response_cannot_change_operation_or_become_another_terminal_receipt():
    command, payload = command_and_payload('runtime.supervision.respond')
    record = receipt(command, payload)
    previous = SupervisionReceiptObservation.observe(command, record, readback=payload)
    changed = record.model_dump(mode='json')
    changed['outcome']['binding']['operation_id'] = 'changed-operation'
    with pytest.raises(ValueError, match='receipt_operation_changed'):
        SupervisionReceiptObservation.observe(command,
            SupervisionCommandReceipt.model_validate_json(json.dumps(changed)), previous=previous)
    with pytest.raises(ValueError, match='terminal_receipt_changed'):
        SupervisionReceiptObservation.observe(command, receipt(command, payload, 'rejected'), previous=previous)
    with pytest.raises(ValueError, match='receipt_readback_mismatch'):
        SupervisionReceiptObservation.observe(command, record, readback=payload.model_copy(update={'response_id': 'other'}))


def test_rejection_is_distinct_from_pending_and_cannot_have_a_readback():
    command, payload = command_and_payload('runtime.supervision.cancel')
    rejected = receipt(command, payload, 'rejected')
    assert SupervisionReceiptObservation.observe(command, rejected).status == 'rejected'
    with pytest.raises(ValueError, match='unexpected_receipt_readback'):
        SupervisionReceiptObservation.observe(command, rejected, readback=payload)


def test_retained_readback_is_revalidated_even_when_domain_record_was_directly_constructed():
    command, payload = command_and_payload('runtime.supervision.respond')
    record = receipt(command, payload)
    verified = SupervisionReceiptObservation.observe(command, record, readback=payload)
    forged = replace(verified, readback_canonical=encoded(payload.model_copy(update={'response_id': 'other'})))
    with pytest.raises(ValueError, match='receipt_readback_mismatch'):
        SupervisionReceiptObservation.observe(command, record, previous=forged)
    pending = SupervisionReceiptObservation.observe(command, receipt(command, payload, 'pending'))
    with pytest.raises(ValueError, match='unexpected_previous_readback'):
        SupervisionReceiptObservation.observe(command, record,
            previous=replace(pending, readback_canonical=encoded(payload)))
