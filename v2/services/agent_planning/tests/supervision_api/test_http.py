"""Configured public HTTP intake/readback against actual Planning SQL."""

from dataclasses import replace

import pytest
from amphora_agent_planning.supervision_api import Credentials, create_app
from amphora_agent_planning.supervision_intake import SupervisionIntake
from fastapi.testclient import TestClient
from sqlalchemy import text

from ..supervision_intake.support import command, request

TOKEN = 'fixture-writer-token-000000000000000000000000'
READ = 'fixture-reader-token-000000000000000000000000'
FOREIGN = 'fixture-foreign-token-0000000000000000000000'


def client(e):
    readonly = replace(e.principal, actions=frozenset({'read_attempts'}))
    foreign = replace(e.principal, scope=e.principal.scope.model_copy(update={'project_id': 'foreign'}))
    credentials = Credentials([(TOKEN, e.principal), (READ, readonly), (FOREIGN, foreign)])
    return TestClient(create_app(SupervisionIntake(e.engine), credentials))


def post(client, path, incoming, token=TOKEN):
    return client.post(path, content=incoming.canonical_bytes,
                       headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})


def test_http_exact_recording_replay_and_read_only_receipt(stored):
    e = stored
    http = client(e)
    value = request(e.principal)
    incoming = command(value)
    assert http.get('/ready').json() == {'status': 'ready', 'mode': 'supervisor_intake_only'}
    assert post(http, '/v1/supervision/receipts/query', incoming, READ).status_code == 404
    first = post(http, '/v1/supervision/requests', incoming)
    assert first.status_code == 200 and first.json()['outcome']['status'] == 'recorded'
    assert post(http, '/v1/supervision/requests', incoming).json() == first.json()
    assert post(http, '/v1/supervision/receipts/query', incoming, READ).json() == first.json()
    path = '/v1/supervision/requests/' + value.planning_request.reference.engagement_id
    observed = http.get(path, headers={'Authorization': 'Bearer ' + READ})
    assert observed.status_code == 200 and observed.json() == value.model_dump(mode='json')
    assert post(http, '/v1/supervision/requests', incoming, READ).status_code == 403
    assert http.get(path, headers={'Authorization': 'Bearer ' + FOREIGN}).status_code == 404
    with e.engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM planning.attempts WHERE tenant_id=:tenant AND project_id=:project'),
            {'tenant': e.principal.scope.tenant_id, 'project': e.principal.scope.project_id}).scalar_one() == 0
    schema = http.get('/openapi.json').json()
    assert schema['paths']['/v1/supervision/requests']['post']['security']


def test_http_auth_scope_and_changed_command_conflict(stored):
    http = client(stored)
    value = request(stored.principal)
    incoming = command(value)
    assert http.post('/v1/supervision/requests', content=incoming.canonical_bytes).status_code == 401
    assert post(http, '/v1/supervision/requests', incoming, 'wrong').status_code == 401
    assert post(http, '/v1/supervision/requests', incoming, FOREIGN).status_code == 403
    post(http, '/v1/supervision/requests', incoming)
    changed = command(value.model_copy(update={'checkpoint_id': 'changed'}))
    assert post(http, '/v1/supervision/requests', changed).status_code == 409
    assert post(http, '/v1/supervision/receipts/query', changed, READ).status_code == 409
    assert post(http, '/v1/supervision/requests?actor=other', incoming).status_code == 422
    denied = post(http, '/v1/supervision/requests', command(value.model_copy(update={'checkpoint_id': 'changed'}), 'new'))
    assert denied.status_code == 200 and denied.json()['outcome']['status'] == 'rejected'


@pytest.mark.parametrize('body,status', [(b'not-json', 422), (b'{"secret":"do-not-echo"}', 422),
                                       (b' ' * 262145, 413), (b'[' * 70 + b'0' + b']' * 70, 422)],
                         ids=['malformed', 'invalid-command', 'oversized', 'deep'])
def test_invalid_or_unbounded_bodies_are_redacted(stored, body, status):
    result = client(stored).post('/v1/supervision/requests', content=body, headers={'Authorization': 'Bearer ' + TOKEN})
    assert result.status_code == status and 'do-not-echo' not in result.text


def test_default_app_is_not_a_provider_or_recording_service():
    http = TestClient(create_app())
    assert http.get('/live').json() == {'status': 'live'}
    assert http.get('/ready').status_code == 503
    assert http.post('/v1/supervision/requests', json={}).status_code == 404
    with pytest.raises(ValueError, match='complete_supervision_configuration_required'):
        create_app(intake=object())
