"""Synthetic owner-computed decisions with scripted producer evidence; no live proof claim."""
from dataclasses import replace
import json

from amphora_contracts_candidate_canonicalization import CanonicalCandidate
from amphora_contracts_evaluation_identity import EvaluationIdentityInput
from amphora_contracts_research import CandidateRevision
from amphora_contracts_synthetic_evaluation import SyntheticEvaluationReceipt
from amphora_research.eligibility.decision import prepare as eligibility_decision
from amphora_research.synthesis.decision import prepare as synthesis_decision
from amphora_research.evaluation_reuse.evidence import CanonicalEvidence, EvaluationEvidence
from amphora_research.evaluation_reuse.policy import ReusePolicy, ReuseSubjects
from amphora_research.fitness.reuse import EvaluationKey

from ..eligibility import test_policy as eligibility
from ..synthesis import test_policy as synthesis
from ..fitness.assembly_fixtures import inputs
from .fixtures import Data, artifact, producer


def bundle(*, required=False, eligibility_status='supported', synthesis_status='unknown', different_context=False):
    _, oldkey, _ = inputs()
    body=oldkey.record.model_dump(mode='json');scope=oldkey.record.context.scope
    body['policy']['purpose']='synthetic-cache-qualification'
    body['policy']['method']['evaluator']['capability_id']='synthetic.digest-score'
    body['policy']['objectives']=[dict(body['policy']['objectives'][0],objective_id='synthetic-digest-score',unit='1',direction='minimize')]
    body['policy']['required_context']=['conditions'];body['policy']['material_state_required']=False
    body['context']['inputs']=[item for item in body['context']['inputs'] if item['name']=='conditions']
    body['context']['material_state']=None
    data=Data(); keys=[];canon=[];candidates=[]
    canonicalizer=oldkey.record.policy.method.evaluator.model_copy(update={'capability_id':'synthetic.polymer-canonicalize'})
    for name,raw in [('source',b'{"fixture":1}'),('target',b'{ "fixture":1 }')]:
        source=artifact(scope,'candidate-'+name,raw,oldkey.record.representation.source.schema_ref);data.contents[source.artifact_id]=raw
        record=json.loads(json.dumps(body));record['representation']['source']=source.model_dump(mode='json')
        if name=='target' and different_context:
            record['context']['inputs'][0]['artifact']['sha256']='e'*64
            record['context']['inputs'][0]['artifact']['artifact_id']='conditions-target'
        declared=EvaluationIdentityInput.model_validate_json(json.dumps(record));key=EvaluationKey(declared);keys.append(key)
        candidate=CandidateRevision(wire_version='1',reference=eligibility.CANDIDATE.model_copy(update={'candidate_id':name}),representation=source,supersedes=None)
        candidates.append(candidate)
        receipt={'wire_version':'1','authority':'synthetic_encoding','scope':scope.model_dump(mode='json'),
            'kind':'polymer','semantic_profile':declared.representation.policy.semantic_profile.model_dump(mode='json'),
            'equivalence_profile':declared.representation.policy.equivalence_profile.model_dump(mode='json'),
            'source_sha256':source.sha256,'canonical_sha256':declared.representation.canonical_sha256}
        output=data.add(scope,name+'-canonical',receipt,CanonicalCandidate,'candidate-canonicalization.receipt')
        canon.append(CanonicalEvidence.resolve(producer(source,output,canonicalizer),canonicalizer,declared,data))
    target=keys[1];evaluation=keys[0].record.policy
    ep=eligibility.policy();ec=replace(ep.context,purpose=evaluation.purpose,
        subject=replace(ep.context.subject,candidate=candidates[1].reference,material_state=None,sample=None),
        conditions=target.record.context.inputs[0].artifact)
    ep=replace(ep,context=ec,reference=evaluation.method.applicability)
    ed=eligibility_decision(ep,(replace(eligibility.claim(disposition=eligibility_status),context=ec),),'fixture','reuse-eligibility').record
    sp=synthesis.policy();sc=replace(sp.context,candidate=candidates[1].reference,purpose=evaluation.purpose,
        conditions=ec.conditions,scale=None,purity=None)
    sp=replace(sp,context=sc,reference=evaluation.synthesis_policy)
    option=synthesis.option(status=synthesis_status);option=replace(option,evidence=replace(option.evidence,context=sc))
    sd=synthesis_decision(sp,(option,),'fixture','reuse-synthesis').record
    identity=data.add(scope,'identity',keys[0].record.model_dump(mode='json'),EvaluationIdentityInput,'evaluation-identity.input')
    receipt={'wire_version':'1','authority':'synthetic_evaluation','scope':scope.model_dump(mode='json'),
        'input_sha256':identity.sha256,'canonical_sha256':keys[0].record.representation.canonical_sha256,
        'method':evaluation.method.model_dump(mode='json'),'objective_id':'synthetic-digest-score','unit':'1','value':13421772}
    output=data.add(scope,'evaluation',receipt,SyntheticEvaluationReceipt,'synthetic-evaluation.receipt')
    evidence=EvaluationEvidence.resolve(producer(identity,output,evaluation.method.evaluator),evaluation,identity,data)
    return ReusePolicy(scope,evaluation,canonicalizer,required),*keys,ReuseSubjects(*candidates,ed,sd),*canon,evidence
