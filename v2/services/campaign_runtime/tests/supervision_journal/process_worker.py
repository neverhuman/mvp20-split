"""Explicit installed-process probe; secrets arrive only through environment."""

import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import sys
import time
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_campaign_runtime.supervision_journal import RequestFrame
from amphora_campaign_runtime.supervision_journal.delivery import DeliveryJournal
from amphora_campaign_runtime.supervision_journal.delivery_values import DeliveryLease
from amphora_campaign_runtime.supervision_journal.responses import ResponseJournal
from amphora_campaign_runtime.supervision_journal.storage import (
    RequestJournal,
    StoredRequest,
)
from amphora_contracts_core import Scope
from amphora_contracts_supervision import SupervisionRef, parse_supervision_command
from sqlalchemy import create_engine, text

from .test_delivery import receipt
from .test_responses import incoming
from .test_series import next_frame
from .test_storage import command, setup

STATE = Path(os.environ['AMPHORA_JOURNAL_PROBE_STATE'])
OUTPUT = Path(os.environ['AMPHORA_JOURNAL_PROBE_OUTPUT'])
MODE = os.environ['AMPHORA_JOURNAL_PROBE_MODE']


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def barrier():
    path = os.environ.get('AMPHORA_JOURNAL_PROBE_BARRIER')
    if path:
        Path(str(OUTPUT) + '.ready').write_text('ready', encoding='utf-8')
        deadline = time.monotonic() + 30
        while not Path(path).exists():
            assert time.monotonic() < deadline, 'process barrier timeout'
            time.sleep(0.02)


@pytest.fixture
def fixture_env():
    assert importlib.metadata.version('amphora-campaign-runtime') == '0.26.0'
    import amphora_campaign_runtime
    assert Path(amphora_campaign_runtime.__file__).absolute().is_relative_to(Path(sys.prefix).absolute())
    assert all(importlib.util.find_spec(name) is None for name in
        ('amphora_agent_planning', 'amphora_research', 'amphora_knowledge', 'amphora_data_artifacts', 'amphora_capability_registry'))
    metadata = json.loads(STATE.read_bytes())
    engine = create_engine(os.environ['AMPHORA_JOURNAL_PROBE_SQL_URL'],
                           connect_args={'options': '-c statement_timeout=8000'})
    scope = Scope.model_validate_json(json.dumps(metadata['scope']))
    principal = RuntimePrincipal('worker-1', scope,
        frozenset({'read', 'admit', 'maintain', 'supervise_prepare', 'supervise_dispatch'}))
    try:
        yield SimpleNamespace(engine=engine, principal=principal)
    finally:
        engine.dispose()


def original(e):
    data = json.loads(STATE.read_bytes())
    frame = RequestFrame.from_bytes(base64.b64decode(data['frame'], validate=True))
    requests = RequestJournal(e.engine, {(e.principal.scope.tenant_id, e.principal.scope.project_id,
                                         e.principal.actor_id): frame.request.planning_request.actor_id})
    return data, frame, requests


def stored(record):
    return {'frame_sha256': record.frame.sha256, 'request_sha256': record.frame.request_sha256,
        'command_sha256': hashlib.sha256(record.canonical_command).hexdigest(),
        'created_at': record.created_at.isoformat(), 'intent_created_at': record.intent_created_at.isoformat()}


def wait_expiry(engine, params):
    with engine.connect() as conn:
        remaining = conn.execute(text('SELECT greatest(0,extract(epoch from expires_at-clock_timestamp())) '
            'FROM runtime.supervision_delivery WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run'), params).scalar_one()
        assert remaining <= 6, 'unexpected lease duration'
        conn.execute(text('SELECT pg_sleep(:seconds)'), {'seconds': float(remaining) + 0.05})


def test_process_stage(graph_env, monkeypatch):
    e = graph_env.env
    if MODE == 'cleanup':
        with e.engine.begin() as conn:
            conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE tenant_id=:tenant AND project_id=:project "
                "AND status='running'"), {'tenant': e.principal.scope.tenant_id, 'project': e.principal.scope.project_id})
        write(OUTPUT, {'stage': MODE, 'scoped_cleanup': True})
        return
    if MODE == 'initialize':
        e, _, frame, params = setup(graph_env)
        incoming_command, capture = incoming(frame, name='abstain')
        data = {'scope': e.principal.scope.model_dump(mode='json'), 'params': params,
            'frame': base64.b64encode(frame.canonical).decode(), 'outgoing': base64.b64encode(command(frame)).decode(),
            'incoming': base64.b64encode(incoming_command.canonical_bytes).decode(),
            'capture': base64.b64encode(capture).decode()}
        write(STATE, data)
        write(OUTPUT, {'stage': MODE, 'run_id': params['run'], 'frame_sha256': frame.sha256})
        return
    data, frame, requests = original(e)
    outgoing = base64.b64decode(data['outgoing'])
    delivery = DeliveryJournal(requests)
    reference = frame.request.reference
    params = data['params']
    barrier()
    if MODE == 'kill_prepare_before_commit':
        def killed(row):
            write(OUTPUT, {'stage': MODE, 'barrier': 'both_inserts_before_commit'})
            os._exit(91)
        monkeypatch.setattr(StoredRequest, 'from_row', killed)
        requests.prepare(e.principal, frame, outgoing)
        raise AssertionError('kill barrier not reached')
    elif MODE == 'inspect_empty':
        assert requests.series(e.principal, params['run'], params['decision']) == ()
        with e.engine.connect() as conn:
            assert conn.execute(text('SELECT count(*) FROM runtime.supervision_outbox WHERE tenant_id=:tenant '
                'AND project_id=:project AND run_id=:run'), params).scalar_one() == 0
        write(OUTPUT, {'stage': MODE, 'rollback': True})
    elif MODE == 'prepare':
        write(OUTPUT, stored(requests.prepare(e.principal, frame, outgoing)))
    elif MODE == 'successor_race':
        successor = next_frame(frame, prepared_by=e.principal.actor_id)
        try:
            saved = requests.prepare(e.principal, successor, command(successor, OUTPUT.stem))
        except ValueError as error:
            assert str(error) == 'request_identity_conflict'
            write(OUTPUT, {'stage': MODE, 'outcome': 'conflict'})
        else:
            write(OUTPUT, {'stage': MODE, 'outcome': 'recorded', **stored(saved)})
    elif MODE == 'changed_retry':
        changed = frame.request.model_copy(update={'deadline_unix_ms': frame.request.deadline_unix_ms - 1})
        alternative = RequestFrame.capture(changed, frame.footprint(), prepared_by=e.principal.actor_id,
                                           planning_actor=changed.planning_request.actor_id)
        with pytest.raises(ValueError, match='request_identity_conflict'):
            requests.prepare(e.principal, alternative, command(alternative))
        write(OUTPUT, {'stage': MODE, 'changed_retry_rejected': True})
    elif MODE == 'claim':
        lease = delivery.claim(e.principal, reference, frame.request_sha256, event_id=OUTPUT.stem, seconds=5)
        write(OUTPUT, {'stage': MODE, 'lease': None if lease is None else lease.record})
    elif MODE == 'kill_after_claim':
        wait_expiry(e.engine, params)
        lease = delivery.claim(e.principal, reference, frame.request_sha256, event_id='dead-holder', seconds=5)
        assert lease is not None
        data['dead_lease'] = lease.record
        write(STATE, data)
        write(OUTPUT, {'stage': MODE, 'barrier': 'lease_committed', 'fence': lease.fence})
        os._exit(93)
    elif MODE == 'recover_delivery':
        wait_expiry(e.engine, params)
        lease = delivery.claim(e.principal, reference, frame.request_sha256, event_id='replacement-holder', seconds=30)
        old = data['dead_lease']
        dead = DeliveryLease(SupervisionRef.model_validate_json(json.dumps(old['reference'])),
            old['request_sha256'], old['holder'], old['fence'], datetime.fromisoformat(old['expires_at']))
        assert lease.fence > dead.fence
        with pytest.raises(ValueError, match='delivery_lease_lost'):
            delivery.observe(e.principal, dead, event_id='stale-append', reason='uncertain')
        event = delivery.observe(e.principal, lease, event_id='original-reconciled',
            receipt=receipt(frame), readback=frame.request)
        assert event.kind == 'recorded'
        write(OUTPUT, {'stage': MODE, 'fence': lease.fence, 'event': event.event_id,
                       'delivery_created_at': event.created_at.isoformat(),
                       **stored(requests.series(e.principal, params['run'], params['decision'])[0])})
    else:
        responses = ResponseJournal(requests)
        principal = replace(e.principal, actor_id=frame.request.planning_request.actor_id,
                            actions=frozenset({'read', 'supervise_respond'}))
        incoming_command = parse_supervision_command('runtime.supervision.respond', base64.b64decode(data['incoming']))
        capture = base64.b64decode(data['capture'])
        if MODE == 'kill_response_before_commit':
            def killed(*args):
                write(OUTPUT, {'stage': MODE, 'barrier': 'response_inserted_before_receipt_commit'})
                os._exit(94)
            monkeypatch.setattr(type(requests.leases.commands), 'finish', killed)
            responses.record(principal, incoming_command, capture_bytes=capture)
            raise AssertionError('kill barrier not reached')
        elif MODE == 'inspect_response_pending':
            assert responses.response(principal, 'response-1') is None
            assert responses.receipt(principal, incoming_command) is None
            write(OUTPUT, {'stage': MODE, 'rolled_back_response': True})
        elif MODE in {'kill_response_after_commit', 'recover_response'}:
            result = responses.record(principal, incoming_command, capture_bytes=capture)
            saved = responses.response(principal, 'response-1')
            snapshot = {'receipt': result.model_dump(mode='json'), 'created_at': saved.created_at.isoformat(),
                'response_sha256': saved.bound.sha256, 'capture_sha256': hashlib.sha256(saved.capture_bytes).hexdigest()}
            if MODE == 'kill_response_after_commit':
                data['response_snapshot'] = snapshot
                write(STATE, data)
                write(OUTPUT, {'stage': MODE, 'barrier': 'response_and_receipt_committed'})
                os._exit(95)
            assert snapshot == data['response_snapshot']
            assert responses.receipt(replace(principal, actions=frozenset({'read'})), incoming_command) == result
            write(OUTPUT, {'stage': MODE, **snapshot})
        else:
            raise AssertionError('unknown process stage')
