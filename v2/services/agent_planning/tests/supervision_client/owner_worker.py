"""Explicit installed Planning client/own-history proof; synthetic capture only."""

import base64
import importlib.metadata
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest
from amphora_agent_planning.supervision_client import (
    ExchangeDenied,
    ExchangeUnavailable,
    ExchangeWindow,
    RuntimeClient,
)
from amphora_contracts_supervision import (
    parse_checkpoint_command,
    parse_supervision_command,
)
from sqlalchemy import create_engine, text

STATE = Path(os.environ['SUPERVISOR_OWNER_STATE'])
OUTPUT = Path(os.environ['SUPERVISOR_OWNER_OUTPUT'])
MODE = os.environ['SUPERVISOR_OWNER_MODE']


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def test_owner_stage():
    assert importlib.metadata.version('amphora-agent-planning') == '0.75.0'
    import amphora_agent_planning
    assert Path(amphora_agent_planning.__file__).absolute().is_relative_to(Path(sys.prefix).absolute())
    assert all(importlib.util.find_spec(name) is None for name in
               ('amphora_campaign_runtime', 'amphora_data_artifacts', 'amphora_research', 'amphora_knowledge'))
    data = json.loads(STATE.read_bytes())
    envelope = data['response_envelope']
    response = parse_supervision_command('runtime.supervision.respond', json.dumps(envelope))
    cancel = parse_supervision_command('runtime.supervision.cancel', json.dumps({
        'encoding': 'amphora-command-v2', 'identity': {**response.identity.model_dump(mode='json'),
        'command_family': 'runtime.supervision.cancel', 'command_id': 'cancel-1'},
        'payload': {'cancellation_id': 'cancel-1', 'reference': envelope['payload']['reference'],
                    'request_sha256': envelope['payload']['request_sha256'], 'reason_code': 'fixture_history_only'}}))
    client = RuntimeClient(response.identity.actor_id, response.identity.scope,
                           os.environ['SUPERVISOR_RUNTIME_ENDPOINT'], os.environ['SUPERVISOR_PEER_TOKEN'])
    if MODE == 'send_response':
        with pytest.raises(ExchangeUnavailable):
            client.submit(response, ExchangeWindow(), guard=lambda: None)
        write(OUTPUT, {'response': 'uncertain'})
        return
    if MODE == 'fresh_denied' or MODE == 'fresh_regranted':
        alternate = json.loads(response.canonical_bytes)
        alternate['identity']['command_id'] = 'fresh-response'
        alternate['payload']['response_id'] = 'fresh-response'
        fresh = parse_supervision_command('runtime.supervision.respond', json.dumps(alternate))
        if MODE == 'fresh_denied':
            with pytest.raises(ExchangeDenied):
                client.submit(fresh, ExchangeWindow(), guard=lambda: None)
            write(OUTPUT, {'fresh_response': 'denied'})
        else:
            observed = client.submit(fresh, ExchangeWindow(), guard=lambda: None)
            assert client.readback(fresh, observed, ExchangeWindow()).status == 'recorded'
            write(OUTPUT, {'fresh_response': 'recorded'})
        return
    if MODE == 'recover_response':
        observed = client.receipt(response, ExchangeWindow())
        observed = client.readback(response, observed, ExchangeWindow())
        cancelled = client.submit(cancel, ExchangeWindow(), guard=lambda: None)
        cancelled = client.readback(cancel, cancelled, ExchangeWindow())
    else:
        assert MODE == 'replay'
        # The exact write itself must recover history before fresh Data processing.
        observed = client.submit(response, ExchangeWindow(), guard=lambda: None)
        observed = client.readback(response, observed, ExchangeWindow())
        cancelled = client.receipt(cancel, ExchangeWindow())
        cancelled = client.readback(cancel, cancelled, ExchangeWindow())
    assert observed.status == cancelled.status == 'recorded'
    engine = create_engine(os.environ['SUPERVISOR_PLANNING_SQL'], connect_args={'options': '-c statement_timeout=5000'})
    try:
        params = {'tenant': data['scope']['tenant_id'], 'project': data['scope']['project_id']}
        with engine.connect() as conn:
            assert conn.execute(text('SELECT count(*) FROM planning.attempts WHERE tenant_id=:tenant AND project_id=:project'), params).scalar_one() == 0
            rows = conn.execute(text('SELECT canonical_request,recorded_at FROM planning.supervision_requests '
                'WHERE tenant_id=:tenant AND project_id=:project'), params).all()
            assert len(rows) == 1
            original = parse_checkpoint_command(base64.b64decode(data['outgoing']))
            assert json.loads(bytes(rows[0][0])) == json.loads(original.canonical_bytes)['payload']
            created = rows[0][1].isoformat()
    finally:
        engine.dispose()
    write(OUTPUT, {'response_receipt': observed.document().model_dump(mode='json'),
                  'cancellation_receipt': cancelled.document().model_dump(mode='json'),
                  'request_recorded_at': created, 'attempts': 0})
