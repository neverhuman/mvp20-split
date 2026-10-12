import json
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from amphora_agent_planning.supervision_api.app import create_app
from amphora_agent_planning.supervision_api.credentials import Credentials
from amphora_agent_planning.supervision_intake import SupervisionIntake
from amphora_agent_planning.curation_intake.configuration import policy_ids
from .support import environment


def test_public_submit_lost_reply_recovery_and_scoped_reads(stored):
    principal, raw, journal = environment(stored)
    readonly = replace(principal, actions=frozenset({'read_curations'}))
    credentials = Credentials([('w' * 40, principal), ('r' * 40, readonly)])
    with TestClient(create_app(SupervisionIntake(stored.engine), credentials, curations=journal)) as client:
        headers = {'Authorization': 'Bearer ' + 'w' * 40}
        assert client.post('/v1/campaign-curations', content=raw).status_code == 401
        first = client.post('/v1/campaign-curations', content=raw, headers=headers)
        assert first.status_code == 200
        receipt = first.json()
        retry = client.post('/v1/campaign-curations', content=raw, headers=headers)
        assert retry.content == first.content
        assert first.headers['cache-control'] == 'no-store'
        query = {'identity': receipt['identity'], 'request_sha256': receipt['request_sha256']}
        read_headers = {'Authorization': 'Bearer ' + 'r' * 40}
        recovered = client.post('/v1/campaign-curations/receipts/query', json=query, headers=read_headers)
        assert recovered.content == first.content
        view = client.get('/v1/campaign-curations/' + receipt['reference']['curation_id'], headers=read_headers)
        assert view.status_code == 200 and view.json()['receipt']['phase'] == 'queued'
        assert client.post('/v1/campaign-curations', content=raw, headers=read_headers).status_code == 403
        changed = json.loads(raw)
        changed['payload']['direction'] = 'Another direction'
        assert client.post('/v1/campaign-curations', json=changed, headers=headers).status_code == 409
        assert client.post('/v1/campaign-curations', content=b' ' * 262145, headers=headers).status_code == 413
        assert client.post('/v1/campaign-curations/receipts/query', content='{"identity":{},"identity":{}}', headers=read_headers).status_code == 422
        assert client.get('/v1/campaign-curations/missing', headers=read_headers).status_code == 404
        assert client.get('/ready').status_code == 200


@pytest.mark.parametrize('raw', ['{}', '[1]', '["same","same"]', '["bad policy"]', ' ' * 8193])
def test_closed_operator_policy_configuration(raw):
    with pytest.raises(ValueError): policy_ids(raw)


def test_retired_policy_config_can_serve_history():
    assert policy_ids('[]') == frozenset()
