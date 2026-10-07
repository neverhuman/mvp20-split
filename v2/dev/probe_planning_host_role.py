"""Actual isolated Planning host role probe against only the dedicated deployment."""

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import time
import urllib.request

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle import ProcessJob
from amphora_deployment.persistence.state import LocalState


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--installation',type=Path,required=True)
    parser.add_argument('--role',choices=['planning_migrator','planning_service'],required=True)
    args=parser.parse_args()
    root=Path(os.environ['LOCALAPPDATA'])/'Amphora/local-v2/installation'
    state=LocalState.snapshot(root)
    bundle=CredentialVault(root/'credentials.dpapi',state['deployment_id']).load()
    name='PG_'+args.role.upper()+'_PASSWORD'
    password=bundle.environment([name])[name]
    token=bundle.environment(['PLANNING_OPERATOR_TOKEN'])['PLANNING_OPERATOR_TOKEN']
    environment={key:value for key,value in os.environ.items() if key.upper() in {'SYSTEMROOT','WINDIR','PATH','TEMP','TMP','COMSPEC','USERPROFILE','LOCALAPPDATA','APPDATA'}}
    environment['AMPHORA_PLANNING_DATABASE_URL']='postgresql+psycopg://'+args.role+':'+password+'@127.0.0.1:'+str(state['postgres']['port'])+'/amphora_local'
    environment['AMPHORA_PLANNING_SUPERVISION_CREDENTIALS']=json.dumps([{'token':token,'actor_id':'operator','scope':{'tenant_id':'internal','project_id':'demo'},'actions':['read_attempts']}])
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1',0));port=reserve.getsockname()[1]
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    result={'role':args.role,'served_ready':False,'exit_code':None}
    with ProcessJob() as job:
        process=subprocess.Popen([str(args.installation/'environment/Scripts/python.exe'),'-I','-m','amphora_agent_planning.supervision_api','--host','127.0.0.1','--port',str(port)],
            env=environment,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
        job.attach(process)
        try:
            deadline=time.monotonic()+25
            while time.monotonic()<deadline and process.poll() is None:
                try:
                    with opener.open('http://127.0.0.1:'+str(port)+'/ready',timeout=1) as response:
                        value=json.loads(response.read(8192))
                        result['served_ready']=response.status==200 and value.get('status')=='ready'
                        break
                except OSError:time.sleep(.1)
            result['exit_code']=process.poll()
        finally:
            job.close();process.wait(timeout=10)
    print(json.dumps(result))


if __name__=='__main__':
    try:main()
    except Exception:raise SystemExit('Planning host role probe failed; raw diagnostics suppressed.') from None
