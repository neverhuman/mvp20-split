import json
import pytest
from ..transport.test_http import launch_api
from .test_journal import successor


def test_scoped_successor_read_query_and_replay(launch_api):
    request, fresh, journal, available, _ = launch_api
    intent = successor(fresh); root='/v1/campaign-successor-launches'
    assert request(root,intent.request.canonical_bytes,authenticated=False)[0]==401
    assert request(root,fresh.request.canonical_bytes)[0]==422
    assert request('/v1/campaign-launches',intent.request.canonical_bytes)[0]==422
    first=request(root,intent.request.canonical_bytes)
    assert first[0]==202 and first[1]['predecessor']==intent.predecessor.model_dump(mode='json')
    assert request(root,intent.request.canonical_bytes)==first
    assert request('/v1/campaign-launches/launch-1')[0]==404
    assert request(root+'/launch-1')==(200,first[1])
    query={'identity':intent.request.identity.model_dump(mode='json'),'request_sha256':intent.request.sha256}
    available[0]=False
    assert request(root+'/receipts/query',json.dumps(query).encode())==(200,first[1])
    query['request_sha256']='0'*64
    assert request(root+'/receipts/query',json.dumps(query).encode())[0]==409
    query['identity']['actor_id']='other'
    assert request(root+'/receipts/query',json.dumps(query).encode())[0]==403
    assert journal.active().intent==intent


@pytest.mark.parametrize('path,body',[
    ('/receipts/query',b'{}'),('/receipts/query',b'{"identity":{},"identity":{}}'),
    ('?run=other',b'{}'),('/receipts/query/extra',b'{}'),('/launch-1',b'{}')])
def test_rejected_shapes_create_no_work(launch_api,path,body):
    request,_,journal,_,_=launch_api
    assert request('/v1/campaign-successor-launches'+path,body)[0] in {404,422}
    assert journal.active() is None
