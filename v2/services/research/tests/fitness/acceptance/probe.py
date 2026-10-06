"""SDK-only controller for actual Data/Research HTTP; owner fixture bootstrap is explicit."""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).absolute().parents[5]
spec = importlib.util.spec_from_file_location('fitness_http_support',ROOT/'sdk/tool_protocol/tests/acceptance/support.py')
HTTP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(HTTP)


def main(config):
    assert all(importlib.util.find_spec(name) is None for name in ('sqlalchemy','amphora_research','amphora_data_artifacts'))
    root = Path(config['evidence']);root.mkdir()
    scope = {'tenant_id':'fitness-http','project_id':uuid.uuid4().hex}
    tokens = {name:uuid.uuid4().hex for name in ('uploader','research','fixture')}
    resources = []
    def principal(actor,actions):
        return {'actor_id':actor,'scope':scope,'actions':actions,'token_env':'TOKEN_'+actor.upper()}
    def command(family,payload):
        return {'identity':{'scope':scope,'actor_id':'uploader','command_family':family,'command_id':uuid.uuid4().hex},'payload':payload}
    def schema(name,body):
        path=root/(name+'.json');path.write_bytes(body)
        return {'schema_id':name,'version':'1','sha256':hashlib.sha256(body).hexdigest(),'media_type':'application/json','schema_path':path.name}
    profiles=[schema('fixture.fitness-source',b'{"type":"object"}')]
    for name in ('candidate-space.polymer','evaluation-identity.input'):
        profiles.append(schema(name,(ROOT/'contracts/schemas/v1'/(name+'.validation.json')).read_bytes()))
    references={item['schema_id']:{k:item[k] for k in ('schema_id','version','sha256')} for item in profiles}
    (root/'storage').mkdir()
    data_config={'database_url_env':'DATABASE_URL','storage_root':str(root/'storage'),'profiles':profiles,
        'principals':[principal('uploader',['upload','finalize','read']),principal('research',['read'])]}
    def start(name,module,body,database,port=None):
        path=root/(name+'.json');path.write_text(json.dumps(body),encoding='utf-8')
        env=dict(HTTP.isolated_env(),DATABASE_URL=os.environ[database])
        env.update({'TOKEN_'+name.upper():value for name,value in tokens.items()})
        host=HTTP.Service(config[name],module,path,env,root,port or HTTP.free_port());resources.append(host)
        host.ready(tokens['fixture'] if name=='research' else tokens['uploader'],'/health' if name=='research' else '/ready')
        return host
    try:
        data=start('artifact','amphora_data_artifacts',data_config,'AMPHORA_ARTIFACT_DATABASE_URL')
        def publish(body,name):
            content={'sha256':hashlib.sha256(body).hexdigest(),'size_bytes':len(body),'media_type':'application/json','schema_ref':references[name]}
            uploaded=HTTP.decoded(data.endpoint,'/v1/uploads',tokens['uploader'],command('artifacts.begin_upload',{'content':content}))
            assert HTTP.request(data.endpoint,'/v1/uploads/'+uploaded['upload_id']+'/content',tokens['uploader'],body,'PUT')[0]==200
            return HTTP.decoded(data.endpoint,'/v1/artifacts/finalize',tokens['uploader'],command('artifacts.finalize',{'upload_id':uploaded['upload_id'],'content':content}))['artifact']
        template=json.loads(Path(__file__).with_name('fixture.json').read_bytes())
        def scopes(value):
            if isinstance(value,dict):
                if set(value)=={'tenant_id','project_id'}:return scope
                return {k:scopes(v) for k,v in value.items()}
            if isinstance(value,list):return [scopes(v) for v in value]
            return value
        template=scopes(template)
        candidate_id=template['evidence']['candidate']['representation']['artifact_id']
        replacements={candidate_id:publish(json.dumps(template['design']).encode(),'candidate-space.polymer')}
        def sources(value):
            if isinstance(value,dict):
                if {'artifact_id','schema_ref','media_type','size_bytes','scope','sha256'}==set(value):
                    name=value['artifact_id']
                    if name not in replacements:replacements[name]=publish(json.dumps({'fixture_source':name}).encode(),'fixture.fitness-source')
                    return replacements[name]
                return {k:sources(v) for k,v in value.items()}
            if isinstance(value,list):return [sources(v) for v in value]
            return value
        template=sources(template)
        path=root/'owner-input.json';path.write_text(json.dumps(template),encoding='utf-8')
        result=subprocess.run([config['research'],'-I',str(Path(__file__).with_name('bootstrap.py')),str(path)],
            env=dict(HTTP.isolated_env(),AMPHORA_RESEARCH_DATABASE_URL=os.environ['AMPHORA_RESEARCH_DATABASE_URL']),
            cwd=root,capture_output=True,text=True,encoding='utf-8',timeout=60)
        (root/'bootstrap.log').write_text(result.stderr,encoding='utf-8')
        assert result.returncode==0,'Research bootstrap failed; inspect bootstrap.log'
        prepared=json.loads(result.stdout)
        identity=publish(json.dumps(prepared['identity']).encode(),'evaluation-identity.input')
        request=prepared['request']|{'declared_identity':identity}
        data_peer={'endpoint':data.endpoint,'token_env':'TOKEN_RESEARCH'}
        research_config={'database_url_env':'DATABASE_URL','principals':[principal('fixture',
            ['assemble_fitness','read_fitness','read_candidate','read_observation_interpretation','read_scientific_record'])],
            'fitness':{'profiles':[prepared['profile']],'data':data_peer},
            'science':{'lab_profiles':[],'eligibility_profiles':[],'synthesis_profiles':[],'consumer_publishers':[],
                'data':data_peer,'publication':{'actor_id':'research','token_env':'TOKEN_RESEARCH'}}}
        research=start('research','amphora_research',research_config,'AMPHORA_RESEARCH_DATABASE_URL')
        accepted=HTTP.decoded(research.endpoint,'/v1/fitness',tokens['fixture'],request)
        assert accepted['disposition']=='ready' and accepted['axes'][0]['value']['value']=='1.25'
        assert accepted['reuse_authority']=='none' and accepted['identity']['authority']=='identity_only'
        assert accepted['synthesis_status']=='unknown' and 'synthesis_unknown' in accepted['focus']
        assert HTTP.decoded(research.endpoint,'/v1/fitness',tokens['fixture'],request)==accepted
        port=research.port;research.close()
        research=start('research','amphora_research',research_config,'AMPHORA_RESEARCH_DATABASE_URL',port)
        selection={'scope':scope,'fitness_id':request['fitness_id']}
        assert HTTP.decoded(research.endpoint,'/v1/fitness/read',tokens['fixture'],selection)==accepted
        assert HTTP.decoded(research.endpoint,'/v1/fitness',tokens['fixture'],request)==accepted
        (root/'artifact-original.json').write_text(json.dumps(data_config,indent=2),encoding='utf-8')
        data_config['principals']=[item for item in data_config['principals'] if item['actor_id']!='research']
        port=data.port;data.close()
        data=start('artifact','amphora_data_artifacts',data_config,'AMPHORA_ARTIFACT_DATABASE_URL',port)
        status,_=HTTP.request(research.endpoint,'/v1/fitness',tokens['fixture'],request)
        assert status==403
        assert HTTP.decoded(research.endpoint,'/v1/fitness/read',tokens['fixture'],selection)==accepted
        evidence={'status':'passed','timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'scope':scope,
            'fitness':accepted['reference'],'source_count':len(accepted['sources']),'packages':config['packages'],
            'replay_after_research_restart':True,'current_denial':403,'historical_read_after_denial':200,
            'limits':'Actual Data/Research HTTP with Research-owned synthetic bootstrap; declared identity only, no producer-backed reuse, science, image or target-host claim'}
        (root/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(evidence))
    finally:
        for resource in reversed(resources):resource.close()


if __name__=='__main__':main(json.loads(Path(sys.argv[1]).read_bytes()))
