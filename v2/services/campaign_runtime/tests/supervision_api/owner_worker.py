"""Explicit installed Runtime owner probe; never imports a peer implementation."""

import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.lifecycle.access import RuntimePrincipal
from amphora_campaign_runtime.supervision_client import (
    ExchangeUnavailable,
    ExchangeWindow,
    PlanningClient,
)
from amphora_campaign_runtime.supervision_journal import RequestFrame
from amphora_campaign_runtime.supervision_journal.cancellations import (
    CancellationJournal,
)
from amphora_campaign_runtime.supervision_journal.delivery import DeliveryJournal
from amphora_campaign_runtime.supervision_journal.responses import ResponseJournal
from amphora_campaign_runtime.supervision_journal.storage import RequestJournal
from amphora_contracts_core import Scope
from amphora_contracts_supervision import SupervisionRequest, parse_supervision_command
from sqlalchemy import create_engine, text

from ..supervision_journal.test_responses import incoming
from ..supervision_journal.test_storage import command, setup

STATE = Path(os.environ['SUPERVISOR_OWNER_STATE'])
OUTPUT = Path(os.environ['SUPERVISOR_OWNER_OUTPUT'])
MODE = os.environ['SUPERVISOR_OWNER_MODE']


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


@pytest.fixture
def fixture_env():
    assert importlib.metadata.version('amphora-campaign-runtime') == '0.29.0'
    import amphora_campaign_runtime
    assert Path(amphora_campaign_runtime.__file__).absolute().is_relative_to(Path(sys.prefix).absolute())
    assert all(importlib.util.find_spec(name) is None for name in
               ('amphora_agent_planning', 'amphora_data_artifacts', 'amphora_research', 'amphora_knowledge'))
    data = json.loads(STATE.read_bytes())
    engine = create_engine(os.environ['SUPERVISOR_RUNTIME_SQL'], connect_args={'options': '-c statement_timeout=5000'})
    principal = RuntimePrincipal('worker-1', Scope.model_validate_json(json.dumps(data['scope'])),
        frozenset({'read', 'admit', 'maintain', 'supervise_prepare', 'supervise_dispatch'}))
    try:
        yield SimpleNamespace(engine=engine, principal=principal)
    finally:
        engine.dispose()


def test_owner_stage(graph_env):
    e = graph_env.env
    if MODE == 'cleanup':
        with e.engine.begin() as conn:
            conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE tenant_id=:tenant "
                "AND project_id=:project AND status='running'"),
                {'tenant': e.principal.scope.tenant_id, 'project': e.principal.scope.project_id})
        write(OUTPUT, {'scoped_cleanup': True})
        return
    if MODE == 'bootstrap':
        e, journal, frame, params = setup(graph_env)
        original = journal.prepare(e.principal, frame, command(frame))
        response, capture = incoming(frame, name='abstain')
        data = {'scope': e.principal.scope.model_dump(mode='json'), 'params': params,
                'frame': base64.b64encode(frame.canonical).decode(),
                'outgoing': base64.b64encode(original.canonical_command).decode(),
                'response_envelope': json.loads(response.canonical_bytes),
                'capture': base64.b64encode(capture).decode(),
                'original_created_at': original.created_at.isoformat(),
                'original_intent_at': original.intent_created_at.isoformat()}
        write(STATE, data)
        write(OUTPUT, {'run_id': params['run'], 'request_sha256': frame.request_sha256})
        return
    data = json.loads(STATE.read_bytes())
    frame = RequestFrame.from_bytes(base64.b64decode(data['frame'], validate=True))
    journal = RequestJournal(e.engine, {})
    original = journal.series(e.principal, data['params']['run'], data['params']['decision'])[0]
    assert original.created_at.isoformat() == data['original_created_at']
    assert original.intent_created_at.isoformat() == data['original_intent_at']
    assert original.canonical_command == base64.b64decode(data['outgoing'])
    delivery = DeliveryJournal(journal)
    outgoing = parse_supervision_command('planning.supervision.request', original.canonical_command)
    if MODE in {'send_request', 'recover_request'}:
        lease = delivery.claim(e.principal, frame.request.reference, frame.request_sha256, event_id=MODE, seconds=60)
        assert lease is not None
        client = PlanningClient(outgoing.identity.actor_id, outgoing.identity.scope,
                                os.environ['SUPERVISOR_PLANNING_ENDPOINT'], os.environ['SUPERVISOR_PEER_TOKEN'])
        def guard():
            with e.engine.connect() as conn:
                row = conn.execute(text('SELECT fence,holder,expires_at>clock_timestamp() AS live FROM runtime.supervision_delivery '
                    'WHERE tenant_id=:tenant AND project_id=:project AND run_id=:run AND decision_id=:decision '
                    'AND request_sha256=:request'), {**data['params'], 'request': frame.request_sha256}).mappings().one()
            assert row['live'] and row['fence'] == lease.fence and row['holder'] == e.principal.actor_id
        if MODE == 'send_request':
            with pytest.raises(ExchangeUnavailable):
                client.submit(outgoing, ExchangeWindow(), guard=guard)
            saved = delivery.observe(e.principal, lease, event_id='request-lost-reply', reason='reply_lost')
            assert saved.kind == 'unknown'
            write(OUTPUT, {'delivery': saved.kind})
        else:
            window = ExchangeWindow()
            observed = client.receipt(outgoing, window)
            observed = client.readback(outgoing, observed, window)
            saved = delivery.observe(e.principal, lease, event_id='request-recovered', receipt=observed.document(),
                                     readback=SupervisionRequest.model_validate_json(observed.readback_canonical))
            assert saved.kind == 'recorded'
            write(OUTPUT, {'delivery': saved.kind, 'receipt': observed.document().model_dump(mode='json')})
        return
    assert MODE == 'inspect'
    response = ResponseJournal(journal).response(e.principal, 'response-1')
    cancellation = CancellationJournal(journal).cancellation(e.principal, 'cancel-1')
    assert response is not None and cancellation is not None
    assert response.capture_bytes == base64.b64decode(data['capture'])
    events = delivery.history(e.principal, frame.request.reference, frame.request_sha256)
    assert [event.kind for event in events] == ['claim', 'unknown', 'claim', 'recorded']
    with e.engine.connect() as conn:
        status = conn.execute(text('SELECT status FROM runtime.runs WHERE tenant_id=:tenant '
            'AND project_id=:project AND run_id=:run'), data['params']).scalar_one()
    assert status == 'running'
    write(OUTPUT, {'request_created': original.created_at.isoformat(), 'intent_created': original.intent_created_at.isoformat(),
        'response_created': response.created_at.isoformat(), 'cancel_created': cancellation.created_at.isoformat(),
        'response_digest': response.bound.sha256, 'capture_digest': hashlib.sha256(response.capture_bytes).hexdigest(),
        'delivery_receipt': events[-1].evidence.receipt.model_dump(mode='json'), 'run_status': status})
