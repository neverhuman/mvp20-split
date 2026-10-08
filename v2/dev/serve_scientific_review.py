"""Serve a completed scientific fixture for review; never invent qualification evidence."""
import argparse
import hashlib
import json
import shutil
import time
import urllib.parse
import webbrowser
from datetime import datetime,timedelta
from pathlib import Path
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from check_boundaries import ROOT
from local_numeric_configuration import write
from verify_local_browser import BrowserController

def serve(args):
    root=args.root.absolute();run=args.run.absolute();out=args.output.absolute();out.mkdir(parents=True,exist_ok=False)
    evidence=json.loads((run/'evidence.json').read_bytes());assert evidence['status']=='passed' and evidence['provider_calls']==0
    assert len(evidence['result']['reports'])==4 and all(r['result']['scientific_status']=='unvalidated_screen' for r in evidence['result']['reports'])
    public=out/'public';public.mkdir()
    for name in ('index.html','app.js','app.css'):shutil.copyfile(args.public/name,public/name)
    owners=json.loads((run/'owners.json').read_bytes())['owners'];routes=Routes.load(root)
    config={'profile':'local-gateway-v1','public_directory':str(public),
        'peers':{name:{'endpoint':routes.endpoint(name),'token_env':'AMPHORA_'+name.upper()+'_OPERATOR_TOKEN'} for name in owners},
        'context':{'actor_id':'admin','scope':evidence['scope'],'run_id':evidence['run_id'],'synthetic':True},'launcher_key_env':'AMPHORA_GATEWAY_SESSION_KEY'}
    path=write(out/'gateway.json',config)
    owners['gateway']={'installation':str(ROOT.parent/'.test-results/local-gateway-drain-20261006a'),
        'source_lock':str(ROOT.parent/'.test-results/demo-20261008/frozen-original/locks/gateway.lock'),
        'configuration':str(path),'secret_references':['GATEWAY_SESSION_KEY']+[name.upper()+'_OPERATOR_TOKEN' for name in config['peers']]}
    write(out/'owners.json',{'profile':'local-supervisor-v1','owners':owners})
    state=LocalState.snapshot(root);tokens=CredentialVault(root/'credentials.dpapi',state['deployment_id']).load().environment(['GATEWAY_SESSION_KEY','REGISTRY_OPERATOR_TOKEN'])
    controller=BrowserController(root,out,routes,registry_token=tokens['REGISTRY_OPERATOR_TOKEN'])
    try:
        controller.start();origin=routes.endpoint('gateway')
        write(out/'browser-input.json',{'origin':origin,'run_id':evidence['run_id'],'scope':evidence['scope']})
        if args.open_browser:
            code,issued=controller.request(origin,'/launcher/ticket',token=tokens['GATEWAY_SESSION_KEY'],method='POST');assert code==200
            webbrowser.open(origin+'/#view='+args.view+'&launch='+urllib.parse.quote(issued['ticket'],safe=''))
        write(out/'ready.json',{'status':'ready','origin':origin,'run_id':evidence['run_id'],'scope':evidence['scope'],
            'assets':{n:hashlib.sha256((public/n).read_bytes()).hexdigest() for n in ('index.html','app.js','app.css')},
            'timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'scheduled_stop_local':(datetime.now()+timedelta(seconds=args.duration)).strftime('%Y-%m-%d %H:%M:%S'),
            'ui_mode':'scientific_execution_review','provider_calls':0,'workers_started':False,'browser_qualification':'pending_separate_probe'})
        print('Scientific execution review ready: '+origin,flush=True);deadline=time.monotonic()+args.duration
        while time.monotonic()<deadline and not (out/'STOP').exists():
            assert controller.process.poll() is None;time.sleep(.5)
        final=controller.drain();write(out/'drain.json',{'status':'drained','final':final})
    finally:controller.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','run','output','public'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--duration',type=int,default=86400);parser.add_argument('--open',dest='open_browser',action='store_true')
    parser.add_argument('--view',choices=['question','evaluation','execution','knowledge','design'],default='execution')
    args=parser.parse_args();assert 1<=args.duration<=86400;serve(args)
