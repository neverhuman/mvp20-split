from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.reader import AssessmentPeerUnavailable
from amphora_research.transport.access import Credentials
from amphora_research.transport.api import create_app
from amphora_research.transport.host import ResearchHost
from amphora_research.transport.resolver import IdentityResolver

from .storage_fixtures import stored_case

pytestmark = pytest.mark.postgres
HEADERS = {'Authorization':'Bearer '+'s'*32}


def test_routes_authenticate_owner_grants_and_replay_with_history_after_denial(ledger):
    operations,principal,request,reader = stored_case(ledger)
    credentials = Credentials([('s'*32,principal),('r'*32,replace(principal,actions=frozenset({'read_fitness'})))])
    client = TestClient(create_app(IdentityResolver(ledger[0]),credentials,fitness=operations))
    assert client.post('/v1/fitness',json=request.model_dump(mode='json')).status_code == 401
    assert client.post('/v1/fitness',json=request.model_dump(mode='json'),headers={'Authorization':'Bearer '+'r'*32}).status_code == 403
    result = client.post('/v1/fitness',json=request.model_dump(mode='json'),headers=HEADERS)
    assert result.status_code == 200 and result.json()['reuse_authority'] == 'none'
    assert result.headers['cache-control'] == 'no-store'
    assert client.post('/v1/fitness',json=request.model_dump(mode='json'),headers=HEADERS).json() == result.json()
    selection = {'scope':principal.scope.model_dump(mode='json'),'fitness_id':request.fitness_id}
    for error,status in [(AssessmentError('peer_access_denied'),403),(AssessmentPeerUnavailable('peer_deadline'),503)]:
        reader.error = error
        assert client.post('/v1/fitness',json=request.model_dump(mode='json'),headers=HEADERS).status_code == status
        assert client.post('/v1/fitness/read',json=selection,headers=HEADERS).json() == result.json()
    selection['fitness_id'] = 'absent'
    assert client.post('/v1/fitness/read',json=selection,headers=HEADERS).status_code == 404


def test_ref_mismatch_and_foreign_scope_cannot_be_hidden_in_dto(ledger):
    operations,principal,request,_ = stored_case(ledger)
    client = TestClient(create_app(IdentityResolver(ledger[0]),Credentials([('s'*32,principal)]),fitness=operations))
    body = request.model_dump(mode='json')
    body['candidate']['scope']['project_id'] = 'foreign'
    assert client.post('/v1/fitness',json=body,headers=HEADERS).status_code == 403
    body = request.model_dump(mode='json')
    body['interpretation']['sha256'] = 'e'*64
    assert client.post('/v1/fitness',json=body,headers=HEADERS).status_code == 422
    body = request.model_dump(mode='json')
    body['profile']['policy']['sha256'] = 'e'*64
    assert client.post('/v1/fitness',json=body,headers=HEADERS).status_code == 404


def test_invalid_identity_document_is_terminal_422_and_does_not_publish(ledger):
    import hashlib
    operations,principal,request,reader = stored_case(ledger)
    reader.raw = b'{"wire_version":"1","wire_version":"1"}'
    source = request.declared_identity.model_copy(update={'sha256':hashlib.sha256(reader.raw).hexdigest(),'size_bytes':len(reader.raw)})
    reader.source = source
    request = request.model_copy(update={'declared_identity':source})
    client = TestClient(create_app(IdentityResolver(ledger[0]),Credentials([('s'*32,principal)]),fitness=operations))
    response = client.post('/v1/fitness',json=request.model_dump(mode='json'),headers=HEADERS)
    assert response.status_code == 422 and response.json()['code'] == 'fitness_identity_document_invalid'
    from .test_storage import selection
    assert operations.read(principal,selection(request)) is None


@pytest.mark.parametrize('grant',['read_candidate','read_observation_interpretation','read_scientific_record'])
def test_assembly_needs_each_owner_read_grant_before_data_access(ledger,grant):
    operations,principal,request,reader = stored_case(ledger)
    principal = replace(principal,actions=principal.actions-{grant})
    client = TestClient(create_app(IdentityResolver(ledger[0]),Credentials([('s'*32,principal)]),fitness=operations))
    assert client.post('/v1/fitness',json=request.model_dump(mode='json'),headers=HEADERS).status_code == 403
    assert reader.calls == []


def test_host_configuration_uses_explicit_optional_fitness_and_environment_secrets(ledger,monkeypatch):
    operations,principal,request,_ = stored_case(ledger)
    monkeypatch.setenv('FITNESS_TEST_DB',ledger[0].engine.url.render_as_string(hide_password=False))
    monkeypatch.setenv('FITNESS_TEST_TOKEN','s'*32)
    monkeypatch.setenv('FITNESS_TEST_DATA','d'*32)
    config = {'database_url_env':'FITNESS_TEST_DB','principals':[{'token_env':'FITNESS_TEST_TOKEN',
        'actor_id':principal.actor_id,'scope':principal.scope.model_dump(mode='json'),'actions':['read_fitness']}],
        'fitness':{'data':{'endpoint':'http://127.0.0.1:9','token_env':'FITNESS_TEST_DATA'},
                   'profiles':[next(iter(operations.profiles.values())).record.model_dump(mode='json')]}}
    host = ResearchHost.configured(config)
    try:
        assert host.app.state.fitness_enabled
        response = TestClient(host.app).post('/v1/fitness/read',json={'scope':principal.scope.model_dump(mode='json'),'fitness_id':'missing'},headers=HEADERS)
        assert response.status_code == 404
    finally:
        host.close()
    del config['fitness']
    with pytest.raises(ValueError,match='fitness_configuration_required'):
        ResearchHost.configured(config)
