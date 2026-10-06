import json
from types import SimpleNamespace

import pytest
from amphora_agent_planning.evaluation_batch.storage import EvaluationJournal
from amphora_agent_planning.evaluation_execution import EvaluationRunner
from amphora_agent_planning.openai_provider import MODEL, OpenAIProvider
from amphora_agent_planning.openai_provider.evaluation import FrozenOpenAIEvaluation
from openai_evaluation_bundle import load_bundle


def test_entire_frozen_suite_is_bound_before_any_call():
    principal,protocol,batch,provider=load_bundle(None)
    assert len(provider.prepared)==12 and batch.accounting_units==368640000
    assert max(len(item.body) for item in provider.prepared.values())==9277
    assert protocol.manifest.mode=='live'
    provider.validate(protocol,batch)
    with pytest.raises(ValueError,match='evaluation_live_provider'):
        FrozenOpenAIEvaluation(protocol,batch,None)
    wrong=SimpleNamespace(sha256='f'*64)
    with pytest.raises(ValueError,match='evaluation_live_binding'):provider.validate(wrong,batch)
    with pytest.raises(ValueError,match='openai_artifact_binding'):
        FrozenOpenAIEvaluation(protocol,batch,OpenAIProvider(None,lambda ref:b'forged'))
    assert principal.scope==batch.tasks[0].request.document().reference.scope


@pytest.mark.postgres
def test_live_bound_runner_uses_original_durable_issuance_and_replay(stored):
    import hashlib

    from amphora_agent_planning.budget import BudgetPolicy
    from amphora_agent_planning.context import RequestSnapshot
    from amphora_agent_planning.evaluation import EvaluationProtocol
    from amphora_agent_planning.evaluation_batch import EvaluationBatch
    from openai_evaluation_bundle import ROOT
    class Counted:
        calls=0
        def send(self,raw):
            self.calls+=1
            value={'schema_version':'1','action':'abstain','rationale':'Offline binding test.',
                   'entities':[],'assertions':[],'questions':[],'answers':[],'evidence_needs':[],'diagnostics':[]}
            return json.dumps({'model':MODEL,'status':'completed','usage':{'input_tokens':100,'output_tokens':20},
                'output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':json.dumps(value)}]}]}).encode()
    def scope(value):
        if isinstance(value,dict):
            if set(value)=={'tenant_id','project_id'}:return stored.principal.scope.model_dump(mode='json')
            return {key:scope(item) for key,item in value.items()}
        if isinstance(value,list):return [scope(item) for item in value]
        return value
    # A separate test scope prevents offline observations from poisoning paid history.
    inputs=scope(json.loads((ROOT/'inputs.json').read_bytes()))
    manifest=scope(json.loads((ROOT/'manifest.json').read_bytes()))
    corpus=json.loads((ROOT/'corpus.json').read_bytes())
    requests,policies={},{}
    for case_id,value in inputs.items():
        value['request']['actor_id']=stored.principal.actor_id
        requests[case_id]=RequestSnapshot.from_bytes(json.dumps(value['request']).encode(),actor_id=stored.principal.actor_id,scope=stored.principal.scope)
        policies[case_id]=BudgetPolicy.from_bytes(json.dumps(value['policy']).encode())
    for case in corpus['cases']:case['input_sha256']=requests[case['case_id']].sha256
    raw=json.dumps(corpus).encode();manifest['corpus_sha256']=hashlib.sha256(raw).hexdigest()
    protocol=EvaluationProtocol.load(json.dumps(manifest).encode(),raw)
    batch=EvaluationBatch.prepare(protocol,stored.principal,requests,policies)
    bodies=json.loads((ROOT/'bodies.json').read_bytes());transport=Counted()
    provider=FrozenOpenAIEvaluation(protocol,batch,OpenAIProvider(transport,lambda ref:bodies[ref.sha256].encode()))
    EvaluationJournal(stored.engine).register(stored.principal,protocol,batch)
    runner=EvaluationRunner(stored.engine,provider,adapter_revision=provider.revision,timeout_seconds=60)
    first=runner.step(stored.principal,protocol.manifest.suite_id)
    assert first.status=='pending' and not first.passed and transport.calls==1
    assert first.observations[0].observation.status=='scientific_abstention'
    assert runner.read(stored.principal,protocol.manifest.suite_id)==first and transport.calls==1
    replacement=EvaluationRunner(stored.engine,provider,adapter_revision=provider.revision,timeout_seconds=60)
    second=replacement.step(stored.principal,protocol.manifest.suite_id)
    assert len(second.observations)==2 and transport.calls==2
    assert second.observations[0]==first.observations[0]
