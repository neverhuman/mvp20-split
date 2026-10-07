"""Actual seven-process infrastructure proof; never admits campaigns or invokes models."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import uuid

from amphora_deployment.lifecycle import ProcessJob
from amphora_deployment.lifecycle.configuration import control_token, load_bindings
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.lifecycle.health import observe
from amphora_deployment.persistence.docker import Docker
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.persistence.stores import owned


def verify(manifest, output, drain=False, dependency_failure=False, registry_evidence=False, replay_evidence=None):
    output.mkdir(parents=True,exist_ok=False)
    root=Path(os.environ['LOCALAPPDATA'])/'Amphora/local-v2/installation'
    routes=Routes.load(root)
    bindings=load_bindings(root,manifest,routes)
    original_state=LocalState.snapshot(root)
    original_vault=(root/'credentials.dpapi').read_bytes()
    token=control_token(root)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(endpoint,path,token=None,method='GET',body=None):
        headers={} if token is None else {'Authorization':'Bearer '+token}
        if body is not None: headers['Content-Type']='application/json'
        req=urllib.request.Request(endpoint+path,headers=headers,method=method,data=body)
        with opener.open(req,timeout=3) as response:
            return response.status,response.read(65536)
    def control(path,method='GET'):
        return json.loads(request(routes.endpoint('supervisor'),path,token,method)[1])
    evidence={'checked_at':datetime.now().astimezone().isoformat(timespec='seconds'),
              'owners':{},'limits':'Read-only infrastructure only. CLI checks establish startup DB access; static health is liveness, not ongoing DB readiness. No scientific tools, admission or provider calls.'}
    with ProcessJob() as job:
        process=subprocess.Popen([sys.executable,'-I','-m','amphora_deployment.lifecycle','serve',
            '--root',str(root),'--manifest',str(manifest)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW)
        job.attach(process)
        try:
            deadline=time.monotonic()+60
            while True:
                try: control('/status'); break
                except OSError:
                    assert process.poll() is None and time.monotonic()<deadline,'supervisor startup unavailable'
                    time.sleep(.2)
            for owner,binding in bindings.items():
                control('/owners/'+owner+'/start','POST')
                path={'artifact':'/ready','planning':'/ready','registry':'/v1/releases?limit=1','gateway':'/'}.get(owner,'/health')
                secret=binding.environment.get('AMPHORA_'+owner.upper()+'_OPERATOR_TOKEN') if owner=='registry' else None
                deadline=time.monotonic()+60
                while True:
                    try:
                        status,body=request(routes.endpoint(owner),path,secret)
                        assert status==200
                        break
                    except OSError:
                        state=control('/status')['owners'][owner]
                        assert state['state']=='running' and time.monotonic()<deadline,owner+' serving unavailable'
                        time.sleep(.2)
                evidence['owners'][owner]={'path':path,'status':status,'release':binding.installation.release,
                                          'installation':str(binding.directory),
                                          'manifest_sha256':binding.installation.installation_manifest_sha256}
                print(owner,'HTTP',status,flush=True)
            if replay_evidence is not None:
                retained=json.loads(replay_evidence.read_bytes())['durable_receipt']
                registry_token=bindings['registry'].environment['AMPHORA_REGISTRY_OPERATOR_TOKEN']
                status,raw=request(routes.endpoint('registry'),'/v1/registry/register',registry_token,'POST',
                                   json.dumps(retained['command']).encode())
                assert status==200 and json.loads(raw)==retained['original'],'Replacement changed retained receipt'
                evidence['retained_replay']={'command_id':retained['command']['identity']['command_id'],
                    'original_receipt_unchanged':True,'controller_python':sys.executable}
                print('Independent controller preserved original retained Registry receipt',flush=True)
            if dependency_failure:
                original=None
                if registry_evidence:
                    fixture=json.loads(Path('v2/contracts/fixtures/v1/tool_releases.json').read_bytes())[0]
                    command={'identity':{'scope':{'tenant_id':'internal','project_id':'demo'},'actor_id':'operator',
                        'command_id':'outage-'+uuid.uuid4().hex,'command_family':'registry.register'},
                        'payload':{'scope':{'tenant_id':'internal','project_id':'demo'},'descriptor':fixture['descriptor'],
                                   'expected_lock':fixture['lock']}}
                    raw=json.dumps(command).encode()
                    registry_token=bindings['registry'].environment['AMPHORA_REGISTRY_OPERATOR_TOKEN']
                    original=request(routes.endpoint('registry'),'/v1/registry/register',registry_token,'POST',raw)
                    receipt=json.loads(original[1])
                    assert receipt['status']=='accepted' and receipt['release']['status']=='registered'
                    evidence['durable_receipt']={'command':command,'original':receipt}
                    print('Dormant synthetic registration receipt accepted; no activation',flush=True)
                before=observe(bindings)
                evidence['before_outage']=before
                assert before['infrastructure']=='available'
                print('Infrastructure readiness available',flush=True)
                state=LocalState.snapshot(root)
                docker=Docker()
                name=state['postgres']['container']
                owned(docker.inspect('container',name),state['deployment_id'],container=True)
                try:
                    docker.run('stop','--time','10',name)
                    failed=observe(bindings)
                    evidence['during_outage']=failed
                    assert failed['infrastructure']=='unavailable'
                    assert all(row['database']=='unavailable' for owner,row in failed['owners'].items() if owner!='gateway')
                    print('All six owners report database unavailable; gateway remains separate',flush=True)
                finally:
                    docker.run('start',name)
                deadline=time.monotonic()+90
                while True:
                    recovered=observe(bindings)
                    if recovered['infrastructure']=='available': break
                    assert time.monotonic()<deadline,'readiness recovery unavailable'
                evidence['after_outage']=recovered
                if original is not None:
                    replay=request(routes.endpoint('registry'),'/v1/registry/register',registry_token,'POST',raw)
                    assert replay==original,'durable receipt changed after database outage'
                    evidence['durable_receipt']['byte_identical_replay']=True
                    print('Original accepted receipt replayed byte-for-byte after outage',flush=True)
                assert LocalState.snapshot(root)==state
                print('Infrastructure readiness recovered; installation journal unchanged',flush=True)
            for owner in reversed(tuple(bindings)):
                if drain:
                    control('/owners/'+owner+'/drain','POST')
                    deadline=time.monotonic()+50
                    while True:
                        state=control('/status')['owners'][owner]
                        if state['state']=='exited':
                            assert state['drain']=='drained' and state['exit_code']==0,owner+' drain failed'
                            break
                        assert state['drain']!='timed_out' and time.monotonic()<deadline,owner+' drain timed out'
                        time.sleep(.1)
                    evidence['owners'][owner]['drain']=state['drain']
                    print(owner,'drained',flush=True)
                else:
                    assert control('/owners/'+owner+'/force-stop','POST')['state']=='exited'
            control('/shutdown','POST')
            assert process.wait(timeout=15)==0
            assert LocalState.snapshot(root)==original_state and (root/'credentials.dpapi').read_bytes()==original_vault
            evidence['installation_and_vault_unchanged']=True
            evidence['status']='passed'
        finally:
            job.close()
            process.wait(timeout=15)
            (output/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print('Seven-process infrastructure proof passed:',output,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--drain',action='store_true')
    parser.add_argument('--dependency-failure',action='store_true')
    parser.add_argument('--registry-evidence',action='store_true')
    parser.add_argument('--replay-evidence',type=Path)
    args=parser.parse_args()
    if args.registry_evidence and not args.dependency_failure: parser.error('--registry-evidence requires --dependency-failure')
    try: verify(args.manifest,args.output,args.drain,args.dependency_failure,args.registry_evidence,args.replay_evidence)
    except Exception: raise SystemExit('Local infrastructure proof failed; inspect safe evidence and lifecycle events. Raw diagnostics suppressed.') from None
