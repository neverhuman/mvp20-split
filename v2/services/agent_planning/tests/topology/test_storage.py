import copy
import importlib.util
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier
import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import DBAPIError
from amphora_agent_planning.access import Principal
from amphora_agent_planning.topology.document import TopologyDocument
from amphora_agent_planning.topology.resolution import TopologyResolver, TopologyOperations
from amphora_agent_planning.topology.store import TopologyJournal
from amphora_contracts_graph_runtime import GraphRunPageV3
from amphora_contracts_tools import ReleaseSnapshot

spec=importlib.util.spec_from_file_location('topology_store_vectors',Path(__file__).with_name('fixtures.py'))
F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
pytestmark=pytest.mark.postgres


class Peers:
    def __init__(self,state):
        self.state=state;self.denied=False;self.calls=[]
    def parent(self,cut):
        self.calls.append('parent')
        if self.denied:raise PermissionError('planning_access_denied')
        return GraphRunPageV3.model_validate_json(json.dumps({'schema_version':'3','scope':self.state.policy().parent.scope.model_dump(mode='json'),
            'run_id':cut.run_id,'plan_sha256':cut.plan_sha256,'revision':cut.revision,'status':'completed',
            'node_count':2,'budget_limit':6,'reserved':0,'spent':1,'stop_reason':None,'nodes':[],'next_after':None}))
    def release(self,lock):
        self.calls.append('release')
        return next(r for r in self.state.releases() if r.lock==lock)


def setup(stored):
    plan,policy,releases=F.fixture()
    def rescope(value):
        if isinstance(value,dict):
            if set(value)=={'tenant_id','project_id'}:value.update(stored.principal.scope.model_dump(mode='json'))
            for child in value.values():rescope(child)
        elif isinstance(value,list):
            for child in value:rescope(child)
    for value in (plan,policy,releases):rescope(value)
    state=F.bind(plan,policy,releases);actor=replace(stored.principal,actions=frozenset({'propose_topology','read_topology'}))
    peer=Peers(state);journal=TopologyJournal(stored.engine)
    resolver=TopologyResolver([(state.policy(),state.plan())],lambda _scope:peer)
    request=F.request(state,scope=actor.scope.model_dump(mode='json'),proposal_id=uuid.uuid4().hex)
    return actor,request,peer,TopologyOperations(journal,resolver)


def test_immutable_retry_replacement_and_current_denial_history(stored):
    actor,request,peer,ops=setup(stored)
    assert ops.read(actor,request.proposal_id) is None
    result=ops.propose(actor,request)
    calls=len(peer.calls);assert calls==3
    assert ops.propose(actor,request)==result and len(peer.calls)==calls*2
    engine=create_engine(stored.engine.url)
    try:assert TopologyJournal(engine).read(replace(actor,actions=frozenset({'read_topology'})),request.proposal_id).projection==result
    finally:engine.dispose()
    peer.denied=True
    with pytest.raises(PermissionError):ops.propose(actor,request)
    assert ops.read(actor,request.proposal_id)==result
    empty=TopologyOperations(ops.journal,TopologyResolver([],lambda _:peer))
    assert empty.read(actor,request.proposal_id)==result
    with pytest.raises(ValueError,match='topology_profile_unavailable'):empty.propose(actor,request)
    for verb in ('UPDATE planning.topology_proposals SET actor_id=actor_id','DELETE FROM planning.topology_proposals'):
        with pytest.raises(DBAPIError),stored.engine.begin() as conn:
            conn.execute(text(verb+' WHERE tenant_id=:tenant AND project_id=:project'),{'tenant':actor.scope.tenant_id,'project':actor.scope.project_id})
    assert ops.read(actor,request.proposal_id)==result


def test_concurrent_retry_and_changed_request_conflict(stored):
    actor,request,peer,ops=setup(stored);barrier=Barrier(2)
    def run():barrier.wait(5);return ops.propose(actor,request)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run) for _ in range(2)];assert futures[0].result(15)==futures[1].result(15)
    expected=ops.read(actor,request.proposal_id)
    changed=request.model_copy(update={'edit_id':'insert'})
    with pytest.raises(ValueError,match='topology_proposal_conflict'):ops.propose(actor,changed)
    assert ops.read(actor,request.proposal_id)==expected


def test_rejected_proposal_and_denied_scoped_actor(stored):
    actor,request,peer,ops=setup(stored);request=request.model_copy(update={'edit_id':'unreviewed'})
    result=ops.propose(actor,request);assert result.status=='rejected' and peer.calls==['parent']
    assert result.reasons==('topology_edit_not_allowed',)
    with pytest.raises(PermissionError):ops.read(replace(actor,actor_id='foreign'),request.proposal_id)
    with pytest.raises(PermissionError):ops.propose(replace(actor,actions=frozenset({'read_topology'})),request)
    with pytest.raises(PermissionError):ops.read(replace(actor,actions=frozenset({'propose_topology'})),request.proposal_id)
    foreign=replace(actor,scope=actor.scope.model_copy(update={'project_id':'other'}))
    assert ops.read(foreign,request.proposal_id) is None


def test_rollback_leaves_no_partial_record(stored):
    actor,request,peer,ops=setup(stored)
    def fail(conn,cursor,statement,parameters,context,executemany):
        if statement.startswith('INSERT INTO planning.topology_proposals'):raise RuntimeError('injected insert interruption')
    event.listen(stored.engine,'after_cursor_execute',fail)
    try:
        with pytest.raises(RuntimeError,match='injected'):ops.propose(actor,request)
    finally:event.remove(stored.engine,'after_cursor_execute',fail)
    assert ops.read(actor,request.proposal_id) is None
    assert ops.propose(actor,request).status=='proposed'


def test_full_document_reconstruction_rejects_projection_tampering(stored):
    actor,request,peer,ops=setup(stored);record=ops.resolver.resolve(actor,request)
    assert TopologyDocument.load(record.canonical)==record
    body=json.loads(record.canonical);body['projection']['definition']['revision']=999
    with pytest.raises(ValueError):TopologyDocument.load(json.dumps(body).encode())
    assert ops.read(actor,request.proposal_id) is None


def test_late_registry_denial_does_not_publish(stored):
    actor,request,peer,ops=setup(stored)
    def denied(_lock):raise PermissionError('planning_access_denied')
    peer.release=denied
    with pytest.raises(PermissionError):ops.propose(actor,request)
    assert ops.read(actor,request.proposal_id) is None


def test_unknown_insert_target_is_recorded_after_exact_release_read(stored):
    actor,request,peer,ops=setup(stored)
    policy=peer.state.policy().model_dump(mode='json');policy['allowed_edits'][1]['target']['node_id']='unknown'
    from amphora_contracts_topology_search import TopologyPolicy
    policy=TopologyPolicy.model_validate_json(json.dumps(policy))
    resolver=TopologyResolver([(policy,peer.state.plan())],lambda _:peer)
    request=request.model_copy(update={'edit_id':'insert','policy':resolver.profiles[0].reference})
    result=TopologyOperations(ops.journal,resolver).propose(actor,request)
    assert result.status=='rejected' and result.reasons==('topology_target_not_invocation',)
    assert peer.calls==['parent','release']


def test_private_store_rejects_record_from_another_actor(stored):
    actor,request,peer,ops=setup(stored)
    record=ops.resolver.resolve(actor,request)
    with pytest.raises(PermissionError):ops.journal.register(replace(actor,actor_id='foreign'),record)
    assert ops.read(actor,request.proposal_id) is None
