"""Actual immutable cancellation storage, never a winner or run mutation."""

import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.supervision_journal.cancellations import (
    CancellationJournal,
)
from amphora_campaign_runtime.supervision_responses import SupervisionReceiptObservation
from amphora_contracts_supervision import parse_supervision_command
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .test_storage import command, setup


def incoming(frame, actor, *, key='cancel-1', command_id=None, reason='superseded'):
    return parse_supervision_command('runtime.supervision.cancel', json.dumps({
        'encoding': 'amphora-command-v2', 'identity': {'scope': frame.request.reference.scope.model_dump(),
        'actor_id': actor, 'command_family': 'runtime.supervision.cancel', 'command_id': command_id or key},
        'payload': {'cancellation_id': key, 'reference': frame.request.reference.model_dump(mode='json'),
        'request_sha256': frame.request_sha256, 'reason_code': reason}}))


def prepared(g):
    e, requests, frame, params = setup(g)
    requests.prepare(e.principal, frame, command(frame))
    principal = replace(e.principal, actions=frozenset({'read', 'supervise_cancel'}))
    return e, CancellationJournal(requests), principal, frame, params


@pytest.mark.parametrize('planning', [False, True])
def test_recording_is_immutable_history_without_execution_effect(graph_env, planning):
    e, journal, principal, frame, params = prepared(graph_env)
    if planning:
        principal = replace(principal, actor_id=frame.request.planning_request.actor_id)
    request = incoming(frame, principal.actor_id)
    assert journal.receipt(principal, request) is None
    first = journal.record(principal, request)
    saved = journal.cancellation(principal, 'cancel-1')
    assert saved.sequence == 1 and first.outcome.status == 'recorded'
    assert SupervisionReceiptObservation.observe(request, first, readback=saved.bound.document()).status == 'recorded'
    with e.engine.begin() as conn:
        assert conn.execute(text('SELECT status FROM runtime.runs WHERE tenant_id=:tenant '
            'AND project_id=:project AND run_id=:run'), params).scalar_one() == 'running'
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE tenant_id=:tenant "
            'AND project_id=:project AND run_id=:run'), params)
    assert CancellationJournal(journal.requests).record(principal, request) == first
    assert journal.cancellation(principal, 'cancel-1') == saved
    readonly = replace(principal, actions=frozenset({'read'}))
    assert journal.receipt(readonly, request) == first
    assert journal.record(principal, incoming(frame, principal.actor_id, key='late')).outcome.status == 'recorded'


def test_cancellation_rolls_back_with_receipt_and_limits_history(graph_env, monkeypatch):
    _, journal, principal, frame, _ = prepared(graph_env)
    request = incoming(frame, principal.actor_id)
    commands = type(journal.requests.leases.commands)
    finish = commands.finish
    def fail(*args):
        raise RuntimeError('before_receipt')
    monkeypatch.setattr(commands, 'finish', fail)
    with pytest.raises(RuntimeError, match='before_receipt'):
        journal.record(principal, request)
    assert journal.receipt(principal, request) is None
    assert journal.cancellation(principal, 'cancel-1') is None
    monkeypatch.setattr(commands, 'finish', finish)
    for index in range(16):
        assert journal.record(principal, incoming(frame, principal.actor_id, key=f'cancel-{index}')).outcome.status == 'recorded'
    duplicate = incoming(frame, principal.actor_id, command_id='duplicate')
    assert journal.record(principal, duplicate).outcome.reason_code == 'cancellation_identity_conflict'
    excess = incoming(frame, principal.actor_id, key='excess')
    first = journal.record(principal, excess)
    assert first.outcome.reason_code == 'cancellation_history_limit'
    assert journal.record(principal, excess) == first


def test_cancellation_authority_replay_conflict_and_grants(graph_env):
    e, journal, principal, frame, params = prepared(graph_env)
    outsider = replace(principal, actor_id='other')
    with pytest.raises(ValueError, match='cancellation_actor_mismatch'):
        journal.record(outsider, incoming(frame, 'other'))
    request = incoming(frame, principal.actor_id)
    with pytest.raises(ValueError, match='access_denied'):
        journal.record(replace(principal, actions=frozenset({'read'})), request)
    journal.record(principal, request)
    changed = incoming(frame, principal.actor_id, reason='changed')
    with pytest.raises(ValueError):
        journal.record(principal, changed)
    with pytest.raises(ValueError, match='cancellation_command_mismatch'):
        journal.receipt(principal, changed)
    foreign = replace(principal, scope=principal.scope.model_copy(update={'project_id': 'foreign'}))
    assert journal.cancellation(foreign, 'cancel-1') is None
    for statement in ['DELETE FROM runtime.supervision_cancellations',
                      'UPDATE runtime.supervision_cancellations SET actor_id=actor_id']:
        with pytest.raises(DBAPIError), e.engine.begin() as conn:
            conn.execute(text(statement + ' WHERE tenant_id=:tenant AND project_id=:project'), params)
