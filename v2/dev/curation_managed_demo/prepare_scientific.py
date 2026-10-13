"""New frozen scientific output allocation; preserves hash-pinned source bytes."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from amphora_deployment.lifecycle.configuration import load_bindings
from campaign_curation_fixture.session import session
from campaign_curation_fixture.recovery import read
from campaign_curation_fixture.publication import Publication
from campaign_curation_fixture.verify import filtered_environment
from local_numeric_configuration import write


def prepare(root,source,planning,material,output):
    assert read(planning/'manifest.json')['packages']['amphora-agent-planning']=='0.139.0'
    model=read(material);assert model['status']=='passed' and len(model['replays'])==15
    shutil.copytree(source,output)
    def relocate(v):
        if isinstance(v,dict):return {k:relocate(x) for k,x in v.items()}
        if isinstance(v,list):return [relocate(x) for x in v]
        if isinstance(v,str) and v.startswith(str(source)+os.sep):return str(output)+v[len(str(source)):]
        return v
    for name in ('owners','access','native','launch','launch-prepared','gateway','artifact','runtime','registry','knowledge','research','planning'):
        path=output/(name+'.json');original=read(path);moved=relocate(original)
        if original!=moved:write(path,moved)
    for profile in read(output/'artifact.json')['profiles']:
        if profile.get('schema_path'):
            assert hashlib.sha256((output/profile['schema_path']).read_bytes()).hexdigest()==profile['sha256']
    owners=read(output/'owners.json');owners['owners']['planning']['installation']=str(planning);write(output/'owners.json',owners)
    roots=read(output/'curation-roots.json');policy=read(output/'curation-policy.json')
    assert roots['prompt']['sha256']==hashlib.sha256(model['instructions'].encode()).hexdigest()
    with session(root,output) as api:
        schema={k:roots['configuration']['schema_ref'][k] for k in ('schema_id','version','sha256')}
        roots['configuration']=Publication(api,policy['template']['reference']['scope']).publish(
            b'OpenAI gpt-5.4-mini-2026-03-17 Responses v10, same medium reasoning and prompt/schema as v9. '
            b'Max input196608 and output16384, worst-case cost0.221184USD within unchanged0.25USD reservation. '
            b'Exact approved demo remainder; original failed call and holds retained. Synthetic engineering only; no retries.',schema)
    policy['template']['context']['model'].update(configuration=roots['configuration'],tokenizer=model['tokenizer'])
    policy['template']['context']['limits']=model['limits']
    write(output/'curation-roots.json',roots);write(output/'curation-policy.json',policy)
    worker=read(output/'curation-worker.json');worker.update(provider='openai_curation_v1',
        live={'key_env':'AMPHORA_OPENAI_API_KEY','scope':worker['scope'],'egress':'approved_synthetic_engineering_only','timeout_seconds':60})
    write(output/'curation-worker.json',worker)
    # Check is provider-disabled and reads no model key; the original response
    # deadline, single-attempt rule and reservation remain unchanged.
    from amphora_deployment.lifecycle.routes import Routes
    env=filtered_environment();env.update(load_bindings(root,output/'owners.json',Routes.load(root))['planning'].environment)
    with (output/'scientific-check.log').open('wb') as log:
        subprocess.run([str(planning/'environment/Scripts/python.exe'),'-I','-m','amphora_agent_planning.curation_worker',
            'check','--config',str(output/'curation-worker.json')],env=env,stdout=log,stderr=log,check=True,timeout=60)
    prepared=read(output/'managed-prepared.json');prepared.update(status='prepared_v10_live_pending_activation',planning_release='0.139.0',source=str(source))
    write(output/'managed-prepared.json',prepared)
    print('Scientific v10 prepared and checked without provider; original files and reservations preserved',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','source','planning','material','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();prepare(*(Path(os.path.abspath(getattr(args,name))) for name in ('root','source','planning','material','output')))
