"""Fixed independent arithmetic/encoding oracles inside network-disabled images."""
import copy
import hashlib
import json

from check_boundaries import ROOT


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')


def verify_golden(run, images):
    results=[]
    for image in images[:-1]:
        kind=image['module'].removeprefix('amphora_').removesuffix('_space')
        sha=image['image_manifest_digest'].removeprefix('sha256:')
        profiles=json.loads(run(['docker','run','--rm','--network','none',image['tag'],'profiles']))
        request=json.loads((ROOT/'services/research/tests/candidate_registration/acceptance'/(kind+'-request.json')).read_bytes())
        request['source'].update(scope={'tenant_id':'image-golden','project_id':'representation-boundaries'},profile=profiles['profile'])
        request['operator']=profiles['operator']
        source=copy.deepcopy(request['source'])
        # These fixture-specific expected encodings are independently specified:
        # two declared polymer units A/B, sites s0/s1, bond s0->s1 already ordered;
        # exact DNA ACGT; numeric coordinate values explicitly IEEE JSON floats.
        if kind=='numeric':
            for coordinate in source['coordinates']:
                for field in ('value','lower','upper'):coordinate[field]=float(coordinate[field])
        def compute(operation,payload):
            return run(['docker','run','--rm','--network','none','-i',image['tag'],'compute',
                '--operation',operation,'--image-sha256',sha],payload)
        moved=json.loads(compute('move',canonical(request)))
        if kind=='numeric':assert moved['result']['coordinates'][0]['value']==-1
        elif kind=='sequence':assert moved['result']['sequence']=='AGGT'
        else:
            assert [site['unit_id'] for site in moved['result']['sites']]==['A','A']
            assert all(value is None for value in moved['result']['metadata'].values())
        original=canonical(source)
        receipt=json.loads(compute('canonicalize',original))
        assert receipt['canonical_sha256']==hashlib.sha256(original).hexdigest()
        assert receipt['source_sha256']==hashlib.sha256(original).hexdigest()
        assert receipt['semantic_profile']==profiles['profile'] and receipt['equivalence_profile']==profiles['equivalence']
        variant=copy.deepcopy(source)
        if kind=='polymer':
            variant['repeat_units'].reverse();variant['sites'].reverse()
            variant['bonds']=[{'left':'s1','right':'s0'}]
        changed=json.dumps(variant,indent=2).encode()
        repeated=json.loads(compute('canonicalize',changed))
        assert repeated['canonical_sha256']==receipt['canonical_sha256']
        assert repeated['source_sha256']==hashlib.sha256(changed).hexdigest()!=receipt['source_sha256']
        assert run(['docker','run','--rm','--network','none',image['tag'],'schema','--operation','canonicalize','--direction','input']) == (ROOT/'contracts/schemas/v1'/('candidate-space.'+kind+'.validation.json')).read_bytes()
        results.append({'kind':kind,'move_result':moved,'canonicalization':receipt,'alternate_encoding':repeated})
    image=images[-1];sha=image['image_manifest_digest'].removeprefix('sha256:')
    profiles=json.loads(run(['docker','run','--rm','--network','none',image['tag'],'profiles']))
    payload=json.loads((ROOT/'services/research/tests/fitness/fixtures/input.json').read_bytes())
    payload['representation']['canonical_sha256']='123456'+'0'*58
    payload['policy']['purpose']='synthetic-cache-qualification'
    payload['policy']['method']={'evaluator':image['descriptors']['evaluate']['tool']['binding'],
        'method':profiles['method'],'applicability':profiles['applicability']}
    payload['policy']['objectives']=[{'objective_id':'synthetic-digest-score','unit':'1','direction':'minimize',
                                    'uncertainty_policy':profiles['uncertainty']}]
    raw=canonical(payload)
    result=json.loads(run(['docker','run','--rm','--network','none','-i',image['tag'],'compute','--image-sha256',sha],raw))
    assert result['value']==1193046 and result['input_sha256']==hashlib.sha256(raw).hexdigest()
    assert result['authority']=='synthetic_evaluation' and result['method']==payload['policy']['method']
    return {'profile':'representation-fixtures-and-hex123456-v1','representation_oracles':results,'evaluation_oracle':result,
        'claim':'Offline image arithmetic/encoding/CLI only; source references and canonical claim for digest oracle are declared fixture metadata, not owner permission or science.'}
