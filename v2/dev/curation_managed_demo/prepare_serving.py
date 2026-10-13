"""Compose the preserved scientific demo with qualified owners and scoped curation."""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

from amphora_deployment.curation_access import provision_curation_credentials
from campaign_curation_fixture.session import session
from campaign_curation_fixture.recovery import read
from campaign_curation_fixture.publication import Publication
from campaign_curation_fixture.verify import worker_configuration
from curation_live_qualification.configuration import worker_environment
from local_numeric_configuration import write


def prepare(root, source, qualified, planning, deployment, material, inventory, output):
    output.mkdir(parents=True,exist_ok=False)
    assert read(planning/'manifest.json')['packages']['amphora-agent-planning']=='0.138.0'
    assert read(deployment/'manifest.json')['packages']['amphora-deployment']=='0.20.1'
    provision_curation_credentials(root)
    configurations={'owners.json','runtime.json','artifact.json','registry.json','gateway.json',
        'native.json','launch.json','launch-prepared.json','access.json','knowledge.json','research.json','planning.json'}
    def relocate(value):
        if isinstance(value,dict):return {key:relocate(item) for key,item in value.items()}
        if isinstance(value,list):return [relocate(item) for item in value]
        if isinstance(value,str) and value.casefold().startswith((str(source)+os.sep).casefold()):
            return str(output)+value[len(str(source)):]
        return value
    for path in source.glob('*.json'):
        if path.name in configurations:write(output/path.name,relocate(read(path)))
        elif path.name not in {'ready.json','drain.json','browser-input.json'}:
            shutil.copyfile(path,output/path.name)
    shutil.copytree(qualified/'public',output/'public')
    owners=read(output/'owners.json')
    for name,row in owners['owners'].items():
        target=output/(name+'.json')
        if not target.exists():
            write(target,relocate(read(Path(row['configuration']))))
        row['configuration']=str(target)
    scope=read(source/'launch-prepared.json')['scope']
    assert scope=={'tenant_id':'internal','project_id':'knowledge-demo-1b1dc25768334153b58973882627b858'}
    grants={'artifact':('DATA',['read','upload','finalize','source_history']),
        'runtime':('RUNTIME',['read','author','validate']),
        'registry':('REGISTRY',['read','resolve']),
        'knowledge':('KNOWLEDGE',['read_graph']),
        'research':('RESEARCH',['read_declarations'])}
    for owner,(label,actions) in grants.items():
        reference='PLANNING_'+label+'_TOKEN'
        config=read(output/(owner+'.json'))
        assert not any(p['token_env']=='AMPHORA_'+reference for p in config['principals'])
        peer_actor = 'planning-author' if owner in {'runtime','registry'} else 'planning-reader' if owner in {'knowledge','research'} else 'admin'
        config['principals'].append({'token_env':'AMPHORA_'+reference,'actor_id':peer_actor,'scope':scope,'actions':actions})
        write(output/(owner+'.json'),config)
        for name in (owner,'planning'):
            refs=owners['owners'][name]['secret_references']
            if reference not in refs:refs.append(reference)
    v2=Path(__file__).absolute().parents[2]
    owners['owners']['planning'].update(installation=str(planning),source_lock=str(v2/'services/agent_planning/uv.lock'))
    gateway=read(qualified/'owners.json')['owners']['gateway']
    owners['owners']['gateway'].update(installation=gateway['installation'],source_lock=gateway['source_lock'])
    write(output/'planning.json',{'curation_policies':['internal-curation-v1'],'principals':[{
        'actor_id':'admin','scope':scope,'token_env':'AMPHORA_PLANNING_OPERATOR_TOKEN',
        'actions':['record_curations','read_curations','read_capabilities','read_campaign_origin','read_attempts']}]})
    write(output/'owners.json',owners)
    prepared=read(output/'launch-prepared.json');prepared['deployment_python']=str(deployment/'environment/Scripts/python.exe')
    write(output/'launch-prepared.json',prepared)
    expected=read(inventory/'readbacks.json')
    with session(root,output) as api:
        for identity,record in expected['runs'].items():
            assert api.call('runtime','/v3/graph-runs/'+identity)==record
        draft=read(inventory/'inventory-evidence.json')['draft']
        assert api.call('planning','/v1/campaign-origins/'+draft['draft_id']+'?revision='+str(draft['revision'])+
            '&content_sha256='+draft['content_sha256'])==expected['origin']
        publication=Publication(api,scope)
        profile=next(row for row in read(output/'artifact.json')['profiles'] if row['media_type']=='text/plain')
        schema={key:profile[key] for key in ('schema_id','version','sha256')}
        model=read(material)
        roots={name:publication.publish(body,schema) for name,body in (
            ('objective',b'Review and iterate the existing illustrative polymer screening graph. Preserve meaningful scientific criteria, concurrent Hansen solvency and Arrhenius viscosity steps, and visible missing capabilities.'),
            ('policy',b'Internal synthetic engineering demonstration only. No experimental calibration, bioavailability, synthesizability or scientific improvement claim. Exact reviewed tools, sources and Knowledge references only. Changes apply between campaigns. Missing capabilities remain requests, never invented tools.'),
            ('configuration',b'OpenAI gpt-5.4-mini-2026-03-17 Responses v9, reasoning medium, output8192. Synthetic egress only. UI-01.08j allocates only the approved37-slot/9.25USD remainder; prior16/4.05USD reservations remain in the closed qualification allocation. No automatic retries or alternate provider.'),
            ('prompt',model['instructions'].encode()))}
        write(output/'curation-roots.json',roots)
        worker_path=worker_configuration(api,output,scope,roots,model,output)
        worker=read(worker_path)
        worker.update(profile='planning-curation-worker.v2',runtime_actor_id='planning-author',database_url_env='AMPHORA_PLANNING_DATABASE_URL',worker_id='managed-demo-curation',provider='disabled',live=None)
        for name in ('data','runtime','registry','knowledge','research'):
            worker[name]['token_env']='AMPHORA_PLANNING_'+name.upper()+'_TOKEN'
        worker['eligibility']['actor_id']='planning-author'
        write(worker_path,worker)
        # Check using the actual selected owner binding; all peer credentials are
        # directed grants, not operator tokens. No provider/key or job advancement.
        from amphora_deployment.lifecycle.configuration import load_bindings
        bindings=load_bindings(root,output/'owners.json',api.controller.routes)
        environment=worker_environment(root,api)
        environment.update(bindings['planning'].environment)
        with (output/'curation-check.log').open('wb') as log:
            subprocess.run([str(planning/'environment/Scripts/python.exe'),'-I','-m',
                'amphora_agent_planning.curation_worker','check','--config',str(worker_path)],
                env=environment,stdout=log,stderr=log,check=True,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
    native=read(output/'native.json')
    native['workers']['planning-curation']={'configuration':str(output/'curation-worker.json'),
        'source_lock':owners['owners']['planning']['source_lock'],'scope':None}
    write(output/'native.json',native)
    write(output/'managed-prepared.json',{'status':'prepared_provider_disabled','scope':scope,
        'source':str(source),'original_runs':list(expected['runs']),'draft':draft,
        'planning_release':'0.138.0','deployment_release':'0.20.1','gateway_release':'0.7.0',
        'studio_release':'0.34.1','provider_calls':0,'campaigns_launched':0,
        'remaining_gates':['directed full peer/preparation proof','managed live activation','local/LAN browser']})
    print('Scientific demo prepared with scoped curation; provider disabled; originals retained and drained',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','source','qualified','planning','deployment','material','inventory','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    prepare(*(Path(os.path.abspath(getattr(args,name))) for name in
        ('root','source','qualified','planning','deployment','material','inventory','output')))
