"""Bounded managed scientific serving; no automatic campaign or curation request."""
import argparse
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

from amphora_deployment.lifecycle.configuration import load_bindings
from campaign_curation_fixture.session import session, PublicOwners
from campaign_curation_fixture.recovery import read
from campaign_curation_fixture.verify import filtered_environment
from curation_live_qualification.run import credential
from local_numeric_configuration import write


def peer_reads(api, environment, serving, output):
    tokens={name:environment['AMPHORA_PLANNING_'+label+'_TOKEN'] for name,label in
        [('artifact','DATA'),('runtime','RUNTIME'),('registry','REGISTRY'),('knowledge','KNOWLEDGE'),('research','RESEARCH')]}
    peer=PublicOwners(api.controller,tokens,read(serving/'launch-prepared.json')['launch_port'])
    original=read(serving/'public-origin.json')['origin']
    checks=[('runtime','/v1/definition-universe',None),('registry','/v1/releases',None),
        ('knowledge','/v1/graph-snapshots/read',original['knowledge']['head']['snapshot'])]
    checks.extend(('research','/v1/questions/read',question) for question in original['research']['selection']['questions'])
    checks.extend(('artifact','/v1/artifacts/'+artifact['artifact_id'],None) for artifact in read(serving/'curation-roots.json').values())
    checks.extend(('runtime','/v3/graph-runs/'+identity,None) for identity in read(serving/'managed-prepared.json')['original_runs'])
    for owner,path,body in checks:
        assert peer.call(owner,path,body)==api.call(owner,path,body)
    write(output/'peer-read-evidence.json',{'status':'passed','checks':[{'owner':owner,'path':path} for owner,path,_ in checks],
        'matches_operator_readbacks':True,'provider_calls':0,'timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S')})


def serve(root, serving, output, *, duration, live=False):
    output.mkdir(parents=True, exist_ok=False)
    config=read(serving/'curation-worker.json')
    assert (config['provider']=='openai_curation_v1') == live
    assert config['scope']==read(serving/'managed-prepared.json')['scope']
    key=credential(Path('Z:/ssos/.env')) if live else None
    with session(root,serving,model_key=key) as api:
        key=None
        bindings=load_bindings(root,serving/'owners.json',api.controller.routes)
        planning=bindings['planning']
        peer_reads(api,planning.environment,serving,output)
        environment=filtered_environment()
        environment.update(planning.environment)
        interpreter=Path(read(serving/'owners.json')['owners']['planning']['installation'])/'environment/Scripts/python.exe'
        script=Path(__file__).absolute().parents[1]/'curation_live_qualification/allowance.py'
        with (output/'allowance.log').open('wb') as log:
            subprocess.run([str(interpreter),'-I',str(script),str(serving/'curation-worker.json'),str(output/'allowance.json')],
                env=environment,stdout=log,stderr=log,check=True,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
        allowance=read(output/'allowance.json')
        assert allowance['authorization']=='UI-01.08j-demo-remainder'
        assert allowance['maximum_slots']==37 and allowance['maximum_units']==9250000000
        if live:
            assert allowance['remaining_slots']>0
            api.controller.control('/workers/planning-curation/start','POST')
        origin='http://127.0.0.1:57013'
        prepared=read(serving/'managed-prepared.json')
        write(output/'browser-input.json',{'origin':origin,'draft_id':prepared['draft']['draft_id'],
            'scope':config['scope']})
        write(output/'ready.json',{'status':'ready','origin':origin,'scope':config['scope'],
            'serving':str(serving),'live_curation':live,'campaigns_automatically_launched':0,
            'timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'supervisor_pid':api.controller.process.pid,'initial_allowance':allowance})
        print('Managed scientific demo ready at '+origin+'; live curation '+str(live),flush=True)
        deadline=time.monotonic()+duration
        while time.monotonic()<deadline and not (output/'STOP').exists():
            assert api.controller.process.poll() is None,'Managed supervisor exited'
            if live:
                status=api.controller.control('/status')['workers']['planning-curation']
                assert not status['faulted'],'Managed curation fault; inspect retained owner state'
            time.sleep(1)
    write(output/'stopped.json',{'status':'drained','timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S')})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','serving','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--duration',type=int,default=3600)
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    assert 1<=args.duration<=86400
    serve(*(Path(os.path.abspath(getattr(args,name))) for name in ('root','serving','output')),
          duration=args.duration,live=args.live)
