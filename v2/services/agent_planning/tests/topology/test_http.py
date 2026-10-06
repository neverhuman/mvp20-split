"""Actual owned SQL and ASGI API with explicitly scripted current peers."""
import importlib.util
import json
from dataclasses import replace
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from amphora_agent_planning.supervision_api import create_app
from amphora_agent_planning.supervision_api.credentials import Credentials
from amphora_agent_planning.supervision_intake import SupervisionIntake
from amphora_agent_planning.topology.peers import TopologyPeerUnavailable
from amphora_agent_planning.topology.store import TopologyJournal, TopologyStoreUnavailable
from amphora_agent_planning.topology.resolution import TopologyOperations, TopologyResolver

spec=importlib.util.spec_from_file_location('topology_http_vectors',Path(__file__).with_name('test_storage.py'))
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
pytestmark=pytest.mark.postgres
TOKEN='t'*32


def client(stored,actor,ops):
    credentials=Credentials([(TOKEN,actor),('r'*32,replace(actor,actions=frozenset({'read_topology'}))),
        ('f'*32,replace(actor,actor_id='foreign'))])
    return TestClient(create_app(SupervisionIntake(stored.engine),credentials,topology=ops)),credentials


def test_authenticated_proposal_retry_history_and_conflict(stored):
    actor,request,peer,ops=S.setup(stored);app,_=client(stored,actor,ops)
    with app:
        headers={'Authorization':'Bearer '+TOKEN}
        assert app.get('/ready').json()['mode']=='supervisor_intake_and_topology'
        assert app.get('/v1/topology-proposals/'+request.proposal_id,headers=headers).status_code==404
        response=app.post('/v1/topology-proposals',content=request.model_dump_json(),headers=headers)
        assert response.status_code==200 and response.json()['status']=='proposed'
        assert app.post('/v1/topology-proposals',content=request.model_dump_json(),headers=headers).json()==response.json()
        assert app.get('/v1/topology-proposals/'+request.proposal_id,headers=headers).json()==response.json()
        altered=request.model_copy(update={'edit_id':'insert'})
        assert app.post('/v1/topology-proposals',content=altered.model_dump_json(),headers=headers).status_code==409
        peer.denied=True
        assert app.post('/v1/topology-proposals',content=request.model_dump_json(),headers=headers).status_code==403
        assert app.get('/v1/topology-proposals/'+request.proposal_id,headers={'Authorization':'Bearer '+'r'*32}).json()==response.json()
        assert app.get('/v1/topology-proposals/'+request.proposal_id,headers={'Authorization':'Bearer '+'f'*32}).status_code==403
    empty=TopologyOperations(ops.journal,TopologyResolver([],lambda _:peer))
    replacement,_=client(stored,actor,empty)
    with replacement:
        assert replacement.get('/v1/topology-proposals/'+request.proposal_id,headers=headers).json()==response.json()
        assert replacement.post('/v1/topology-proposals',content=request.model_dump_json(),headers=headers).status_code==404


def test_api_denies_untrusted_grants_and_bounds_input(stored):
    actor,request,peer,ops=S.setup(stored);app,_=client(stored,actor,ops)
    with app:
        headers={'Authorization':'Bearer '+TOKEN}
        assert app.post('/v1/topology-proposals',content=request.model_dump_json()).status_code==401
        assert app.post('/v1/topology-proposals',content=request.model_dump_json(),headers={'Authorization':'Bearer '+'r'*32}).status_code==403
        foreign=request.model_copy(update={'scope':request.scope.model_copy(update={'project_id':'other'})})
        assert app.post('/v1/topology-proposals',content=foreign.model_dump_json(),headers=headers).status_code==403
        for body in (b'{"x":1,"x":2}',b'{"x":NaN}',b'{',b'[]'):
            response=app.post('/v1/topology-proposals',content=body,headers=headers)
            assert response.status_code==422 and b'Traceback' not in response.content
        assert app.post('/v1/topology-proposals?bypass=true',content=request.model_dump_json(),headers=headers).status_code==422
        assert app.post('/v1/topology-proposals',content=b'x'*262145,headers=headers).status_code==413
        assert app.get('/v1/topology-proposals/'+'x'*129,headers=headers).json()['reason_code']=='invalid_topology_request'
        assert ops.read(actor,request.proposal_id) is None


def test_peer_and_stored_corruption_are_unavailable_not_client_rejection(stored,monkeypatch):
    actor,request,peer,ops=S.setup(stored);app,_=client(stored,actor,ops)
    with app:
        headers={'Authorization':'Bearer '+TOKEN}
        def unavailable(_cut):raise TopologyPeerUnavailable('fixture private details')
        peer.parent=unavailable
        response=app.post('/v1/topology-proposals',content=request.model_dump_json(),headers=headers)
        assert response.status_code==503 and 'private' not in response.text
        def corrupt(*args):raise TopologyStoreUnavailable('fixture private bytes')
        monkeypatch.setattr(ops.journal,'read',corrupt)
        response=app.get('/v1/topology-proposals/'+request.proposal_id,headers=headers)
        assert response.status_code==503 and 'private' not in response.text
    with pytest.raises(TopologyStoreUnavailable):
        TopologyJournal.decode(actor,{'actor_id':actor.actor_id,'record_bytes':b'{}'})


def test_topology_grants_require_explicit_host_configuration(stored):
    actor,request,peer,ops=S.setup(stored);_,credentials=client(stored,actor,ops)
    with pytest.raises(ValueError,match='topology_configuration_required'):create_app(SupervisionIntake(stored.engine),credentials)
    with pytest.raises(ValueError,match='topology_requires_configured_planning'):create_app(topology=ops)
