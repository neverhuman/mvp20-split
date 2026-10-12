from dataclasses import replace
import json

import pytest
from fastapi.testclient import TestClient

from amphora_agent_planning.curation_intake.journal import CurationJournal
from amphora_agent_planning.supervision_api.app import create_app
from amphora_agent_planning.supervision_api.credentials import Credentials
from amphora_agent_planning.supervision_intake import SupervisionIntake
from .test_intake import setup

pytestmark = pytest.mark.postgres


def test_approved_endpoint_is_scoped_idempotent_intake_only(stored):
    owner, raw, journal = setup(stored)
    reader = replace(owner, actions=frozenset({'read_capabilities'}))
    credentials = Credentials([('w' * 40, owner), ('r' * 40, reader)])
    path = '/v1/capability-requests/' + raw['payload']['request']['request_id'] + '/fulfillments'
    app = create_app(SupervisionIntake(stored.engine), credentials, curations=CurationJournal(stored.engine, ()))
    with TestClient(app) as client:
        assert client.post(path, json=raw).status_code == 401
        assert client.post(path, json=raw, headers={'Authorization': 'Bearer ' + 'r' * 40}).status_code == 403
        headers = {'Authorization': 'Bearer ' + 'w' * 40}
        first = client.post(path, json=raw, headers=headers)
        assert first.status_code == 200 and first.json()['status'] == 'pending'
        assert first.headers['cache-control'] == 'no-store'
        assert client.post(path, json=raw, headers=headers).content == first.content
        assert client.post(path + '?retry=true', json=raw, headers=headers).status_code == 422
        assert client.post('/v1/capability-requests/foreign/fulfillments', json=raw, headers=headers).status_code == 422
        changed = json.loads(json.dumps(raw))
        changed['payload']['release']['descriptor_sha256'] = 'f' * 64
        assert client.post(path, json=changed, headers=headers).status_code == 409
        changed['payload']['request']['request_id'] = 'missing'
        changed['identity']['command_id'] = 'another'
        assert client.post('/v1/capability-requests/missing/fulfillments', json=changed, headers=headers).status_code == 404
        changed['verified'] = True
        assert client.post(path, json=changed, headers=headers).status_code == 422
        visible = client.get(path.removesuffix('/fulfillments'), headers={'Authorization': 'Bearer ' + 'r' * 40})
        assert visible.status_code == 200 and visible.json()['status'] == 'requested'
        assert visible.json()['fulfillment'] == first.json()


def test_fulfillment_credentials_require_explicit_curation_configuration(stored):
    owner = replace(stored.principal, actions=frozenset({'fulfill_capabilities'}))
    with pytest.raises(ValueError, match='curation_configuration_required'):
        create_app(SupervisionIntake(stored.engine), Credentials([('w' * 40, owner)]))
