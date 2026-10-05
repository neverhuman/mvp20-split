"""Captured response history survives uncertainty, rollback and late arrival."""

import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.supervision_journal.responses import ResponseJournal
from amphora_campaign_runtime.supervision_responses import SupervisionReceiptObservation
from amphora_contracts_supervision import SupervisionResponse, parse_supervision_command
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..supervision_responses.support import replace_capture, response
from .test_storage import command, setup


def incoming(frame, *, name='unknown', key='response-1', command_id=None):
    value, capture = response(name)
    data = value.model_dump(mode='json')
    request = frame.request
    data.update(response_id=key, reference=request.reference.model_dump(mode='json'), request_sha256=frame.request_sha256)
    data['observation']['attempt'].update(engagement=request.planning_request.reference.model_dump(mode='json'),
        request_sha256=request.planning_request_sha256)
    if capture is not None:
        data['capture']['scope'] = request.reference.scope.model_dump(mode='json')
        document = json.loads(capture)
        for item in document['unresolved']:
            item['question']['scope'] = request.reference.scope.model_dump(mode='json')
            item['need']['scope'] = request.reference.scope.model_dump(mode='json')
        capture = json.dumps(document, indent=2).encode()
    value = SupervisionResponse.model_validate_json(json.dumps(data))
    if capture is not None:
        value = replace_capture(value, capture, align_proposal=True)
    parsed = parse_supervision_command('runtime.supervision.respond', json.dumps({
        'encoding': 'amphora-command-v2', 'identity': {'scope': request.reference.scope.model_dump(mode='json'),
        'actor_id': request.planning_request.actor_id, 'command_family': 'runtime.supervision.respond',
        'command_id': command_id or key}, 'payload': value.model_dump(mode='json')}))
    return parsed, capture


def prepared(g):
    e, requests, frame, params = setup(g)
    requests.prepare(e.principal, frame, command(frame))
    principal = replace(e.principal, actor_id=frame.request.planning_request.actor_id,
                        actions=frozenset({'supervise_respond', 'read'}))
    return e, ResponseJournal(requests), principal, frame, params


@pytest.mark.parametrize('name', ['unknown', 'abstain'])
def test_exact_captured_history_and_receipt_survive_run_termination(graph_env, name):
    e, journal, principal, frame, params = prepared(graph_env)
    request, capture = incoming(frame, name=name)
    with e.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run"), params)
    receipt = journal.record(principal, request, capture_bytes=capture)
    assert receipt.outcome.status == 'recorded'
    saved = journal.response(principal, 'response-1')
    assert saved.capture_bytes == capture and saved.sequence == 1
    verified = SupervisionReceiptObservation.observe(request, receipt, readback=saved.bound.document())
    assert verified.status == 'recorded'
    replacement = ResponseJournal(journal.requests)
    assert replacement.record(principal, request, capture_bytes=capture) == receipt
    assert replacement.response(principal, 'response-1') == saved
    readonly = replace(principal, actions=frozenset({'read'}))
    assert replacement.receipt(readonly, request) == receipt
    assert replacement.response(readonly, 'response-1') == saved
    if name == 'unknown':
        assert saved.bound.document().observation.usage.accounting_units is None


def test_response_and_receipt_commit_rollback_together(graph_env, monkeypatch):
    _, journal, principal, frame, _ = prepared(graph_env)
    request, capture = incoming(frame)
    commands = journal.requests.leases.commands
    real = type(commands).finish
    def fail(*args):
        raise RuntimeError('response_before_receipt')
    monkeypatch.setattr(type(commands), 'finish', fail)
    with pytest.raises(RuntimeError, match='response_before_receipt'):
        journal.record(principal, request, capture_bytes=capture)
    assert journal.response(principal, 'response-1') is None
    assert journal.receipt(principal, request) is None
    monkeypatch.setattr(type(commands), 'finish', real)
    assert journal.record(principal, request, capture_bytes=capture).outcome.status == 'recorded'


def test_response_identity_and_history_bound_are_terminal_receipts(graph_env):
    _, journal, principal, frame, _ = prepared(graph_env)
    for index in range(64):
        request, capture = incoming(frame, key=f'response-{index}')
        assert journal.record(principal, request, capture_bytes=capture).outcome.status == 'recorded'
    duplicate, capture = incoming(frame, key='response-0', command_id='new-command')
    assert journal.record(principal, duplicate, capture_bytes=capture).outcome.reason_code == 'response_identity_conflict'
    excess, capture = incoming(frame, key='response-64')
    denied = journal.record(principal, excess, capture_bytes=capture)
    assert denied.outcome.reason_code == 'response_history_limit'
    assert journal.record(principal, excess, capture_bytes=capture) == denied
    assert journal.response(principal, 'response-64') is None


def test_response_actor_scope_capture_and_immutable_grants(graph_env):
    e, journal, principal, frame, params = prepared(graph_env)
    request, capture = incoming(frame, name='abstain')
    assert journal.receipt(principal, request) is None
    with pytest.raises(ValueError, match='access_denied'):
        journal.record(replace(principal, actor_id='other'), request, capture_bytes=capture)
    with pytest.raises(ValueError, match='capture_content_mismatch'):
        journal.record(principal, request, capture_bytes=capture + b' ')
    journal.record(principal, request, capture_bytes=capture)
    foreign = replace(principal, scope=principal.scope.model_copy(update={'project_id': 'foreign'}))
    assert journal.response(foreign, 'response-1') is None
    for statement in ('DELETE FROM runtime.supervision_responses',
                      'UPDATE runtime.supervision_responses SET capture_bytes=capture_bytes'):
        with pytest.raises(DBAPIError), e.engine.begin() as conn:
            conn.execute(text(statement + ' WHERE tenant_id=:tenant AND project_id=:project'), params)
