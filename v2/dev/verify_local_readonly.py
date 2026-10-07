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

from amphora_deployment.lifecycle import ProcessJob
from amphora_deployment.lifecycle.configuration import control_token, load_bindings
from amphora_deployment.lifecycle.routes import Routes


def verify(manifest, output):
    output.mkdir(parents=True,exist_ok=False)
    root=Path(os.environ['LOCALAPPDATA'])/'Amphora/local-v2/installation'
    routes=Routes.load(root)
    bindings=load_bindings(root,manifest,routes)
    token=control_token(root)
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def request(endpoint,path,token=None,method='GET'):
        headers={} if token is None else {'Authorization':'Bearer '+token}
        req=urllib.request.Request(endpoint+path,headers=headers,method=method)
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
            for owner in reversed(tuple(bindings)):
                assert control('/owners/'+owner+'/force-stop','POST')['state']=='exited'
            control('/shutdown','POST')
            assert process.wait(timeout=15)==0
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
    args=parser.parse_args()
    try: verify(args.manifest,args.output)
    except Exception: raise SystemExit('Local infrastructure proof failed; inspect safe evidence and lifecycle events. Raw diagnostics suppressed.') from None
