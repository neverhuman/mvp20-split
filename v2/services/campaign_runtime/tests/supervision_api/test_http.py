"""Actual Runtime SQL behind configured HTTP, with explicit capture fault probes."""

import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.hosting import Host
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from amphora_campaign_runtime.supervision_api import SupervisorRecording
from amphora_campaign_runtime.supervision_capture import CaptureUnavailable
from amphora_contracts_supervision import parse_supervision_command
from fastapi.testclient import TestClient
from sqlalchemy import text

from ..supervision_journal.test_cancellations import incoming as cancel_command
from ..supervision_journal.test_responses import incoming, prepared

TOKEN = 'runtime-supervisor-synthetic-writer-000000000000'
READ = 'runtime-supervisor-synthetic-reader-000000000000'
FOREIGN = 'runtime-supervisor-synthetic-foreign-00000000000'


class CaptureProbe:
    def __init__(self, content):
        self.content, self.calls, self.denied = content, 0, False

    def fetch(self, _reference):
        self.calls += 1
        if self.denied:
            raise CaptureUnavailable('capture_processing_denied')
        return self.content


def configured(g, capture=None):
    e, journal, principal, frame, params = prepared(g)
    principal = replace(principal, actions=principal.actions | {'supervise_cancel'})
    credentials = RuntimeCredentials([(TOKEN, principal),
        (READ, replace(principal, actions=frozenset({'read'}))),
        (FOREIGN, replace(principal, actor_id='other'))])
    recording = SupervisorRecording(journal.requests, capture)
    return TestClient(create_app(e.service, credentials, supervision=recording)), recording, principal, frame, params


def post(http, path, command, token=TOKEN):
    return http.post('/v1/supervision/' + path, content=command.canonical_bytes,
                     headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})


def test_receipt_recovery_precedes_fresh_processing_and_read_only_queries(graph_env):
    http, owner, principal, frame, _ = configured(graph_env)
    request, capture = incoming(frame, name='abstain')
    probe = CaptureProbe(capture)
    owner.captures = probe
    assert http.get('/v1/supervision/ready').json()['mode'] == 'supervisor_recording_only'
    assert post(http, 'responses/receipts/query', request, READ).status_code == 404
    first = post(http, 'responses', request)
    assert first.status_code == 200 and first.json()['outcome']['status'] == 'recorded'
    probe.denied = True
    assert post(http, 'responses', request).json() == first.json()
    assert post(http, 'responses/receipts/query', request, READ).json() == first.json()
    assert probe.calls == 1
    observed = http.get('/v1/supervision/responses/response-1', headers={'Authorization': 'Bearer ' + READ})
    assert observed.status_code == 200 and observed.json() == owner.response(principal, 'response-1').model_dump(mode='json')
    fresh, _ = incoming(frame, name='abstain', key='response-2')
    assert post(http, 'responses', fresh).status_code == 403 and probe.calls == 2
    assert owner.response(principal, 'response-2') is None
    schema = http.get('/openapi.json').json()
    assert schema['paths']['/v1/supervision/responses']['post']['security']


def test_diagnostic_and_cancellation_routes_record_without_execution_effect(graph_env):
    http, owner, principal, frame, params = configured(graph_env)
    response, _ = incoming(frame)
    assert post(http, 'responses', response).json()['outcome']['status'] == 'recorded'
    cancel = cancel_command(frame, principal.actor_id)
    first = post(http, 'cancellations', cancel)
    assert first.status_code == 200 and first.json()['outcome']['committed']['kind'] == 'cancellation'
    assert post(http, 'cancellations/receipts/query', cancel, READ).json() == first.json()
    assert post(http, 'cancellations', cancel).json() == first.json()
    observed = http.get('/v1/supervision/cancellations/cancel-1', headers={'Authorization': 'Bearer ' + READ})
    assert observed.json() == owner.cancellation(principal, 'cancel-1').model_dump(mode='json')
    with owner.requests.engine.connect() as conn:
        assert conn.execute(text('SELECT status FROM runtime.runs WHERE tenant_id=:tenant '
            'AND project_id=:project AND run_id=:run'), params).scalar_one() == 'running'


def test_scope_actor_and_changed_pending_identity_fail_before_capture(graph_env):
    probe = CaptureProbe(b'not-used')
    http, owner, _, frame, _ = configured(graph_env, probe)
    request, _ = incoming(frame, name='abstain')
    assert http.post('/v1/supervision/responses', content=request.canonical_bytes).status_code == 401
    assert post(http, 'responses', request, READ).status_code == 403
    assert post(http, 'responses', request, FOREIGN).status_code == 403
    data = json.loads(request.canonical_bytes)
    data['identity']['actor_id'] = 'other'
    foreign = parse_supervision_command('runtime.supervision.respond', json.dumps(data))
    assert post(http, 'responses', foreign, FOREIGN).status_code == 403
    owner.requests.leases.commands.register(request)
    data = json.loads(request.canonical_bytes)
    data['payload']['response_id'] = 'changed'
    changed = parse_supervision_command('runtime.supervision.respond', json.dumps(data))
    assert post(http, 'responses', changed).status_code == 409
    assert post(http, 'responses/receipts/query', changed, READ).status_code == 409
    assert probe.calls == 0


def test_missing_capture_reader_and_invalid_binding_do_not_record(graph_env):
    http, owner, _, frame, _ = configured(graph_env)
    request, _ = incoming(frame, name='abstain')
    assert post(http, 'responses', request).status_code == 503
    owner.captures = CaptureProbe(b'wrong')
    result = post(http, 'responses', request)
    assert result.status_code == 422 and 'wrong' not in result.text
    assert post(http, 'responses/receipts/query', request, READ).status_code == 404
    assert post(http, 'responses?unknown=1', request).status_code == 422
    result = http.post('/v1/supervision/cancellations', content=b'{"private":"do-not-echo"}',
                       headers={'Authorization': 'Bearer ' + TOKEN})
    assert result.status_code == 422 and 'do-not-echo' not in result.text


def test_default_app_has_no_supervisor_routes():
    http = TestClient(create_app())
    assert http.post('/v1/supervision/responses', json={}).status_code == 404
    with pytest.raises(ValueError, match='configured lifecycle'):
        create_app(supervision=object())


def test_host_explicit_configuration_and_env_credentials(graph_env, tmp_path, monkeypatch):
    _, _, principal, _, _ = configured(graph_env)
    e = graph_env.env
    monkeypatch.setenv('SUPERVISOR_TEST_RUNTIME_URL', e.engine.url.render_as_string(hide_password=False))
    monkeypatch.setenv('SUPERVISOR_TEST_RUNTIME_TOKEN', TOKEN)
    monkeypatch.setenv('SUPERVISOR_TEST_DATA_TOKEN', TOKEN)
    config = {'database_url_env': 'SUPERVISOR_TEST_RUNTIME_URL', 'principals': [{
        'token_env': 'SUPERVISOR_TEST_RUNTIME_TOKEN', 'actor_id': principal.actor_id,
        'scope': principal.scope.model_dump(), 'actions': sorted(principal.actions)}],
        'fixtures': [e.raw['payload']], 'supervision': {'capture_data': {
        'endpoint': 'http://127.0.0.1:1', 'token_env': 'SUPERVISOR_TEST_DATA_TOKEN'}}}
    path = tmp_path / 'runtime.json'
    path.write_text(json.dumps(config))
    host = Host.load(path)
    try:
        assert TestClient(host.app()).get('/v1/supervision/ready').status_code == 200
    finally:
        host.close()
    config['supervision'] = {'unknown': True}
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='supervision_configuration'):
        Host.load(path)
