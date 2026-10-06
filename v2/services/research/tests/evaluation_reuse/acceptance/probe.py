"""SDK-only controller; canonicalization/evaluation originate in actual graph workers."""
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def pin(name, value):
    return {'schema_id':name,'version':'1','sha256':hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()}


def main(config):
    assert all(importlib.util.find_spec(name) is None for name in ('sqlalchemy','amphora_research','amphora_campaign_runtime',
        'amphora_data_artifacts','amphora_numeric_space','amphora_polymer_space','amphora_sequence_space','amphora_synthetic_digest'))
    spec=importlib.util.spec_from_file_location('reuse_peers',Path(__file__).with_name('environment.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    HTTP=module.HTTP;root=Path(config['evidence']);root.mkdir()
    e=module.ReuseEnvironment(config,root)
    try:
        e.setup()
        conditions={name:e.publish(json.dumps({'preparation':name}).encode(),'fixture.reuse-context') for name in ('baseline','changed')}
        cases=[];prepared={};reports=[]
        for kind in ('numeric','polymer','sequence'):
            design=json.loads((module.ROOT/'services/research/tests/candidate_registration/acceptance'/(kind+'-request.json')).read_bytes())['source']
            design.update(scope=e.scope,profile=e.semantic[kind]['profile'])
            target=copy.deepcopy(design)
            if kind=='polymer':
                target['repeat_units'].reverse();target['sites'].reverse()
                target['bonds']=[{'left':bond['right'],'right':bond['left']} for bond in reversed(target['bonds'])]
            source_ref=e.publish(json.dumps(design,separators=(',',':')).encode(),'candidate-space.'+kind)
            target_ref=e.publish(json.dumps(target,indent=2).encode(),'candidate-space.'+kind)
            assert source_ref['sha256']!=target_ref['sha256']
            source_producer,source_proof,_,source_receipt=e.run_tool(kind,source_ref)
            target_producer,target_proof,_,target_receipt=e.run_tool(kind,target_ref)
            assert source_receipt['canonical_sha256']==target_receipt['canonical_sha256']
            assert source_receipt['source_sha256']==source_ref['sha256'] and target_receipt['source_sha256']==target_ref['sha256']
            representation={'kind':kind,'semantic_profile':e.semantic[kind]['profile'],'equivalence_profile':e.semantic[kind]['equivalence']}
            policy={'wire_version':'1','purpose':'synthetic-cache-qualification','representation':representation,
                'method':{'evaluator':e.descriptors['digest']['tool']['binding'],'method':e.semantic['digest']['method'],
                          'applicability':e.semantic['digest']['applicability']},
                'synthesis_policy':pin('fixture.synthetic-reuse-synthesis',{'authority':'synthetic','required':False}),
                'objectives':[{'objective_id':'synthetic-digest-score','unit':'1','direction':'minimize','uncertainty_policy':e.semantic['digest']['uncertainty']}],
                'required_context':['conditions'],'material_state_required':False}
            policy['reference']=pin('fixture.synthetic-reuse-evaluation',policy)
            def identity(source,context):
                return {'wire_version':'1','representation':{'scope':e.scope,'policy':representation,
                    'canonical_sha256':source_receipt['canonical_sha256'],'source':source},'policy':policy,
                    'context':{'scope':e.scope,'material_state':None,'inputs':[{'name':'conditions','artifact':context}]}}
            identity_refs={name:e.publish(json.dumps(identity(source,context)).encode(),'evaluation-identity.input')
                for name,source,context in [('source',source_ref,conditions['baseline']),('target',target_ref,conditions['baseline']),
                                            ('changed',target_ref,conditions['changed'])]}
            evaluation_producer,evaluation_proof,evaluation_ref,evaluation=e.run_tool('digest',identity_refs['source'])
            assert evaluation['input_sha256']==identity_refs['source']['sha256']
            assert evaluation['value']==int(source_receipt['canonical_sha256'][:6],16)
            candidates={name:{'wire_version':'1','reference':{'scope':e.scope,'candidate_id':kind+'-'+name,'revision':1},
                'representation':reference,'supersedes':None} for name,reference in [('source',source_ref),('target',target_ref)]}
            case={'kind':kind,'source_candidate':candidates['source'],'target_candidate':candidates['target'],'conditions':conditions,
                'profile':{'wire_version':'1','authority':'synthetic','scope':e.scope,'evaluation':policy,
                    'canonicalizer':e.descriptors[kind]['tool']['binding'],'synthesis_required':False}}
            cases.append(case)
            prepared[kind]={'candidates':candidates,'identities':identity_refs,'source_producer':source_producer,
                'target_producer':target_producer,'evaluation_producer':evaluation_producer,'evaluation':evaluation_ref}
            reports.append({'kind':kind,'source_producer':source_proof,'target_producer':target_proof,'evaluation_producer':evaluation_proof})
        path=root/'owner-input.json';path.write_text(json.dumps(cases),encoding='utf-8')
        result=subprocess.run([config['research'],'-I',str(Path(__file__).with_name('bootstrap.py')),str(path)],
            cwd=root,env=dict(HTTP.isolated_env(),AMPHORA_RESEARCH_DATABASE_URL=os.environ['AMPHORA_RESEARCH_DATABASE_URL']),
            capture_output=True,text=True,encoding='utf-8',timeout=60)
        (root/'bootstrap.log').write_text(result.stderr,encoding='utf-8')
        assert result.returncode==0,'Research-owned bootstrap failed; inspect bootstrap.log'
        owner=json.loads(result.stdout)
        peer={'endpoint':e.artifact.endpoint,'token_env':'TOKEN_RESEARCH'}
        research_config={'database_url_env':'DATABASE_URL','principals':[e.principal('admin',
            ['qualify_evaluation_reuse','read_evaluation_reuse','read_candidate','read_scientific_record'])],
            'reuse':{'profiles':[owner[kind]['profile'] for kind in prepared],'data':peer,
                     'runtime':{'endpoint':e.runtime.endpoint,'token_env':'TOKEN_RESEARCH'}},
            'science':{'lab_profiles':[],'eligibility_profiles':[],'synthesis_profiles':[],
                'consumer_publishers':[],'data':peer,'publication':{'actor_id':'admin','token_env':'TOKEN_ADMIN'}}}
        research=e.research_host(research_config)
        accepted={};requests={}
        for kind,record in prepared.items():
            request={'wire_version':'1','reuse_id':kind+'-reuse','profile':owner[kind]['profile_ref'],
                'source':{'candidate':record['candidates']['source']['reference'],'identity':record['identities']['source'],
                          'canonicalization':record['source_producer']},
                'target':{'candidate':record['candidates']['target']['reference'],'identity':record['identities']['target'],
                          'canonicalization':record['target_producer']},
                'evaluation':record['evaluation_producer'],**owner[kind]['decisions']['baseline']}
            value=HTTP.decoded(research.endpoint,'/v1/evaluation-reuse',e.tokens['admin'],request)
            assert value['status']=='permitted' and value['reusable_artifact']==record['evaluation']
            assert 'synthesis.unknown' in value['focus'] and 'eligibility.accuracy' in value['focus']
            assert HTTP.decoded(research.endpoint,'/v1/evaluation-reuse',e.tokens['admin'],request)==value
            accepted[kind]=value;requests[kind]=request
            changed=copy.deepcopy(request);changed.update(reuse_id=kind+'-miss',**owner[kind]['decisions']['changed'])
            changed['target']['identity']=record['identities']['changed']
            miss=HTTP.decoded(research.endpoint,'/v1/evaluation-reuse',e.tokens['admin'],changed)
            assert miss['status']=='miss' and miss['reusable_artifact'] is None
            forged=copy.deepcopy(request);forged['reuse_id']=kind+'-forged'
            forged['target']['canonicalization']=record['source_producer']
            assert HTTP.request(research.endpoint,'/v1/evaluation-reuse',e.tokens['admin'],forged)[0]==422
        port=research.port;research.close();research=e.research_host(research_config,port)
        for kind,request in requests.items():
            assert HTTP.decoded(research.endpoint,'/v1/evaluation-reuse',e.tokens['admin'],request)==accepted[kind]
        original=copy.deepcopy(e.artifact_config)
        e.artifact_config['principals']=[p for p in e.artifact_config['principals'] if p['actor_id']!='research']
        port=e.artifact.port;e.artifact.close()
        e.artifact=e.host('artifact','amphora_data_artifacts',e.artifact_config,'AMPHORA_ARTIFACT_DATABASE_URL',port)
        for kind,request in requests.items():
            assert HTTP.request(research.endpoint,'/v1/evaluation-reuse',e.tokens['admin'],request)[0]==403
            selection={'scope':e.scope,'reuse_id':request['reuse_id']}
            assert HTTP.decoded(research.endpoint,'/v1/evaluation-reuse/read',e.tokens['admin'],selection)==accepted[kind]
        evidence={'status':'passed','timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'scope':e.scope,
            'packages':config['packages'],'accepted_invocations':9,'cases':reports,
            'decisions':{kind:value['reference'] for kind,value in accepted.items()},'context_misses':3,
            'wrong_producer_rejections':3,'research_restart_replay':True,'current_data_denial':403,'historical_read_after_denial':200,
            'limits':'Actual Windows installed-owner HTTP/graph workers with explicit synthetic owner bootstrap; no lab/scientific validity, Linux image/Registry or target-host claim'}
        (root/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({k:v for k,v in evidence.items() if k not in {'packages','cases'}}))
    finally:e.close()


if __name__=='__main__':main(json.loads(Path(sys.argv[1]).read_bytes()))
