from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from amphora_research.assessment.policy import AssessmentError
from amphora_research.evaluation_reuse.errors import ReusePeerUnavailable
from amphora_research.transport.access import Credentials
from amphora_research.transport.api import create_app
from amphora_research.transport.host import ResearchHost
from amphora_research.transport.resolver import IdentityResolver
from jsonschema import Draft202012Validator
from amphora_contracts_evaluation_reuse import ReuseProjection

from .storage_fixtures import stored_case
from .test_storage import selection

pytestmark=pytest.mark.postgres
HEADERS={'Authorization':'Bearer '+'s'*32}


def test_api_auth_scoped_grants_replay_and_history_after_peer_failures(ledger):
    ops,principal,request,data,runtime=stored_case(ledger)
    credentials=Credentials([('s'*32,principal),('r'*32,replace(principal,actions=frozenset({'read_evaluation_reuse'})))])
    client=TestClient(create_app(IdentityResolver(ledger[0]),credentials,reuse=ops));body=request.model_dump(mode='json')
    assert client.post('/v1/evaluation-reuse',json=body).status_code==401
    assert client.post('/v1/evaluation-reuse',json=body,headers={'Authorization':'Bearer '+'r'*32}).status_code==403
    result=client.post('/v1/evaluation-reuse',json=body,headers=HEADERS)
    assert result.status_code==200 and result.headers['cache-control']=='no-store'
    Draft202012Validator(ReuseProjection.model_json_schema()).validate(result.json())
    assert result.json()['status']=='permitted'
    assert client.post('/v1/evaluation-reuse',json=body,headers=HEADERS).json()==result.json()
    for peer,error,status in ((data,AssessmentError('peer_access_denied'),403),(runtime,ReusePeerUnavailable('runtime_missing'),503)):
        peer.error=error
        response=client.post('/v1/evaluation-reuse',json=body,headers=HEADERS)
        assert response.status_code==status
        assert client.post('/v1/evaluation-reuse/read',json=selection(request).model_dump(mode='json'),headers=HEADERS).json()==result.json()
        peer.error=None


@pytest.mark.parametrize('grant',['read_candidate','read_scientific_record','qualify_evaluation_reuse'])
def test_each_owner_grant_precedes_peer_reads(ledger,grant):
    ops,principal,request,data,runtime=stored_case(ledger)
    client=TestClient(create_app(IdentityResolver(ledger[0]),Credentials([('s'*32,replace(principal,actions=principal.actions-{grant}))]),reuse=ops))
    assert client.post('/v1/evaluation-reuse',json=request.model_dump(mode='json'),headers=HEADERS).status_code==403
    assert not data.calls and not runtime.calls


def test_host_explicit_config_and_history_without_active_profiles(ledger,monkeypatch):
    ops,principal,request,_,_=stored_case(ledger)
    monkeypatch.setenv('REUSE_TEST_DB',ledger[0].engine.url.render_as_string(hide_password=False))
    monkeypatch.setenv('REUSE_TEST_TOKEN','s'*32);monkeypatch.setenv('REUSE_TEST_PEER','p'*32)
    config={'database_url_env':'REUSE_TEST_DB','principals':[{'token_env':'REUSE_TEST_TOKEN','actor_id':'fixture',
        'scope':principal.scope.model_dump(mode='json'),'actions':['read_evaluation_reuse']}],
        'reuse':{'profiles':[],'data':{'endpoint':'http://127.0.0.1:9','token_env':'REUSE_TEST_PEER'},
            'runtime':{'endpoint':'http://127.0.0.1:9','token_env':'REUSE_TEST_PEER'}}}
    host=ResearchHost.configured(config)
    try:
        assert host.app.state.reuse_enabled
        response=TestClient(host.app).post('/v1/evaluation-reuse/read',json=selection(request).model_dump(mode='json'),headers=HEADERS)
        assert response.status_code==404
    finally:host.close()
    config['reuse']['profiles']=[next(iter(ops.profiles.values())).record.model_dump(mode='json')]
    host=ResearchHost.configured(config);host.close()
    del config['reuse']
    with pytest.raises(ValueError,match='reuse_configuration_required'):ResearchHost.configured(config)
