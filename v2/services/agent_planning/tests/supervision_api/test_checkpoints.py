"""Explicit v2 HTTP requests cannot be read or submitted through legacy routes."""

from ..supervision_intake.support import command as old_command
from ..supervision_intake.support import request as old_request
from ..supervision_intake.test_checkpoints import command, request
from .test_http import FOREIGN, READ, client, post


def test_checkpoint_record_replay_readback_and_profile_isolation(stored):
    http = client(stored)
    value = request(stored.principal)
    incoming = command(value)
    assert http.get('/ready').status_code == 200
    assert post(http, '/v2/supervision/receipts/query', incoming, READ).status_code == 404
    first = post(http, '/v2/supervision/requests', incoming)
    assert first.status_code == 200 and first.json()['outcome']['status'] == 'recorded'
    assert post(http, '/v2/supervision/requests', incoming).json() == first.json()
    assert post(http, '/v2/supervision/receipts/query', incoming, READ).json() == first.json()
    suffix = '/supervision/requests/' + value.planning_request.reference.engagement_id
    headers = {'Authorization': 'Bearer ' + READ}
    assert http.get('/v2' + suffix, headers=headers).json() == value.model_dump(mode='json')
    assert http.get('/v1' + suffix, headers=headers).status_code == 409
    assert post(http, '/v1/supervision/requests', incoming).status_code == 422
    assert post(http, '/v1/supervision/receipts/query', incoming).status_code == 422
    assert http.get('/v2' + suffix, headers={'Authorization': 'Bearer ' + FOREIGN}).status_code == 404
    assert http.get('/v2/supervision/requests/missing', headers=headers).status_code == 404
    changed = command(value.model_copy(update={'checkpoint_id': 'changed'}))
    assert post(http, '/v2/supervision/receipts/query', changed, READ).status_code == 409
    assert post(http, '/v2/supervision/requests', incoming, READ).status_code == 403
    assert http.post('/v2/supervision/requests', content=incoming.canonical_bytes).status_code == 401
    assert http.get('/openapi.json').json()['paths']['/v2/supervision/requests']['post']['security']


def test_checkpoint_routes_reject_original_profile_without_losing_original_readback(stored):
    http = client(stored)
    value = old_request(stored.principal)
    incoming = old_command(value)
    assert post(http, '/v1/supervision/requests', incoming).status_code == 200
    assert post(http, '/v2/supervision/requests', incoming).status_code == 422
    assert post(http, '/v2/supervision/receipts/query', incoming).status_code == 422
    suffix = '/supervision/requests/' + value.planning_request.reference.engagement_id
    headers = {'Authorization': 'Bearer ' + READ}
    assert http.get('/v2' + suffix, headers=headers).status_code == 409
    assert http.get('/v1' + suffix, headers=headers).json() == value.model_dump(mode='json')
