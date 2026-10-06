"""Production HTTP client against owned loopback protocol stubs, not actual owners."""
import importlib.util
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from types import SimpleNamespace
import pytest
from amphora_agent_planning.topology.peers import TopologyPeers, TopologyPeerUnavailable
from amphora_tool_protocol import ProtocolError

spec=importlib.util.spec_from_file_location('topology_peer_vectors',Path(__file__).with_name('fixtures.py'))
F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)


@pytest.fixture
def stub():
    state=F.bind(*F.fixture());request=F.request(state)
    graph={'schema_version':'3','scope':F.SCOPE,'run_id':'previous','plan_sha256':state.plan().sha256,'revision':5,
        'status':'completed','node_count':2,'budget_limit':6,'reserved':0,'spent':1,'stop_reason':None,'nodes':[],'next_after':None}
    record=state.releases()[1]
    selected=SimpleNamespace(status=200,raw=None,graph=graph,record=record.model_dump(mode='json'),calls=[],state=state,request=request)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            selected.calls.append((self.path,self.headers.get('Authorization')))
            value=selected.graph if self.path.startswith('/v3/') else selected.record
            body=selected.raw if selected.raw is not None else json.dumps(value).encode()
            self.send_response(selected.status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    endpoint='http://127.0.0.1:'+str(server.server_port)
    selected.peer=TopologyPeers(state.policy().parent.scope,endpoint,'r'*32,endpoint,'g'*32)
    try:yield selected
    finally:server.shutdown();server.server_close();thread.join(5)


def test_exact_authenticated_paths_and_three_read_ceiling(stub):
    peer=stub.peer;cut=stub.request.predecessor;lock=stub.state.releases()[1].lock
    assert peer.parent(cut).plan_sha256==cut.plan_sha256
    assert peer.release(lock).lock==lock
    peer.parent(cut)
    with pytest.raises(ValueError,match='topology_peer_read_limit'):peer.release(lock)
    assert stub.calls==[('/v3/graph-runs/previous?limit=1','Bearer '+'r'*32),
        ('/v1/releases/'+lock.descriptor_sha256,'Bearer '+'g'*32),('/v3/graph-runs/previous?limit=1','Bearer '+'r'*32)]


@pytest.mark.parametrize('status,error',[(401,PermissionError),(403,PermissionError),(404,ValueError),(500,TopologyPeerUnavailable)],ids=['unauthenticated','denied','missing','unavailable'])
@pytest.mark.parametrize('lane',['parent','registry'])
def test_peer_status_is_bounded_and_redacted(stub,status,error,lane):
    stub.status=status;stub.raw=b'fixture-private-source'
    with pytest.raises(error) as caught:
        if lane=='parent':stub.peer.parent(stub.request.predecessor)
        else:stub.peer.release(stub.state.releases()[1].lock)
    assert 'fixture-private-source' not in str(caught.value) and len(stub.calls)==1


@pytest.mark.parametrize('raw',[b'{"x":1,"x":2}',b'{"x":NaN}',bytes([255]),b'[]',b'{',b'{"scope":"foreign"}'],ids=['duplicate','nonfinite','encoding','array','malformed','shape'])
@pytest.mark.parametrize('lane',['parent','registry'])
def test_malformed_owner_documents_do_not_become_proposals(stub,raw,lane):
    stub.raw=raw
    with pytest.raises(TopologyPeerUnavailable,match='topology_peer_protocol_error'):
        if lane=='parent':stub.peer.parent(stub.request.predecessor)
        else:stub.peer.release(stub.state.releases()[1].lock)


def test_transport_failure_has_no_automatic_retry(stub,monkeypatch):
    def fail(*args,**kwargs):raise ValueError('metadata_unavailable')
    monkeypatch.setattr(stub.peer.runtime,'read',fail)
    with pytest.raises(TopologyPeerUnavailable):stub.peer.parent(stub.request.predecessor)
    assert stub.peer.calls==1 and not stub.calls


@pytest.mark.parametrize('field,value',[('revision',6),('plan_sha256','f'*64),('run_id','other'),('scope',{'tenant_id':'foreign','project_id':'policy'})],ids=['cut','plan','run','scope'])
def test_runtime_selection_mismatch_rejects(stub,field,value):
    stub.graph[field]=value
    with pytest.raises(ValueError,match='topology_current_parent_changed'):stub.peer.parent(stub.request.predecessor)


def test_registry_exact_lock_and_scope_checks(stub):
    lock=stub.state.releases()[1].lock
    stub.record['descriptor']['tool']['purpose']='changed'
    with pytest.raises(ValueError,match='registry_lock'):stub.peer.release(lock)


@pytest.mark.parametrize('suffix',['','?limit=2','?limit=1&extra=x','?limit=1&limit=1','?limit=01'],ids=['missing-bound','larger-page','extra-query','duplicate-query','noncanonical-limit'])
def test_runtime_topology_metadata_target_is_closed(suffix):
    from amphora_agent_planning.metadata_reads.targets import target
    with pytest.raises(ValueError):target('runtime','/v3/graph-runs/previous'+suffix)


def test_registry_transport_failure_is_unavailable_without_retry(stub,monkeypatch):
    def fail(*args,**kwargs):raise ProtocolError('fixture connection loss')
    monkeypatch.setattr(stub.peer.registry,'request',fail)
    with pytest.raises(TopologyPeerUnavailable):stub.peer.release(stub.state.releases()[1].lock)
    assert stub.peer.calls==1 and not stub.calls
