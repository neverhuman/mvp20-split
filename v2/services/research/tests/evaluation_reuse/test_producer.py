import json

import pytest
from amphora_contracts_execution_proofs import AcceptedToolExecution
from amphora_research.evaluation_reuse.errors import ReuseError, ReusePeerUnavailable
from amphora_research.evaluation_reuse.producer import ProducerReader, ProducerSelection
from amphora_research.transport.access import AccessDenied
from amphora_tool_protocol import Reply, TransportLost

from .fixtures import declaration, producer


def setup(monkeypatch, response=None):
    record = declaration()
    source = record.representation.source
    proof = producer(source, source.model_copy(update={'artifact_id':'output'}), record.policy.method.evaluator)
    selection = ProducerSelection(record.context.scope, 'run', 'completion')
    reader = ProducerReader('http://127.0.0.1:12345', 'x'*32, record.context.scope)
    calls = []
    def request(method, path, **kwargs):
        calls.append((method,path,kwargs))
        if isinstance(response, Exception):
            raise response
        return response or Reply(200, proof.model_dump_json().encode())
    monkeypatch.setattr(reader._transport, 'request', request)
    return reader, selection, proof, calls


def test_exact_owner_selection_and_bounded_read_budget(monkeypatch):
    reader, selection, proof, calls = setup(monkeypatch)
    assert reader.read(selection) == proof
    assert calls == [('GET','/v1/runs/run/completions/completion/producer',{'limit':262144})]
    reader.read(selection);reader.read(selection)
    with pytest.raises(ReuseError, match='read_limit'):
        reader.read(selection)
    assert len(calls) == 3


@pytest.mark.parametrize('response,error',[(Reply(401,b'secret'),AccessDenied),(Reply(403,b'secret'),AccessDenied),
    (Reply(404,b'secret'),ReuseError),(Reply(503,b'secret'),ReusePeerUnavailable),
    (Reply(302,b'secret'),ReusePeerUnavailable),(TransportLost('transport_lost'),ReusePeerUnavailable),
    (Reply(200,b'{"x":1,"x":2}'),ReusePeerUnavailable),(Reply(200,b'{}'),ReusePeerUnavailable)],
    ids=['unauthorized','denied','missing','unavailable','redirect','lost','duplicate-json','wrong-shape'])
def test_distinct_safe_failure_categories(monkeypatch,response,error):
    reader,selection,_,calls = setup(monkeypatch,response)
    with pytest.raises(error) as caught:
        reader.read(selection)
    assert 'secret' not in str(caught.value) and len(calls)==1


@pytest.mark.parametrize('path,value',[('completion.run_id','foreign'),('completion.completion_id','foreign'),
    ('completion.scope.project_id','foreign'),('completion.canonical_result',False),
    ('invocation.activation_id','foreign'),('invocation.invocation_id','foreign')])
def test_shape_valid_foreign_or_noncanonical_proof_rejects(monkeypatch,path,value):
    reader,selection,proof,_ = setup(monkeypatch)
    raw=proof.model_dump(mode='json');cursor=raw;parts=path.split('.')
    for part in parts[:-1]:cursor=cursor[part]
    cursor[parts[-1]]=value
    monkeypatch.setattr(reader._transport,'request',lambda *_args,**_kwargs:Reply(200,json.dumps(raw).encode()))
    with pytest.raises(ReuseError):reader.read(selection)


def test_untrusted_paths_and_foreign_scope_never_reach_transport(monkeypatch):
    reader,selection,_,calls=setup(monkeypatch)
    for path in ('../other','run?x=y','run\n','x'*129,''):
        with pytest.raises(ReuseError):ProducerSelection(selection.scope,path,'completion')
    foreign=ProducerSelection(selection.scope.model_copy(update={'project_id':'other'}),'run','completion')
    with pytest.raises(ReuseError,match='scope_mismatch'):reader.read(foreign)
    assert not calls
