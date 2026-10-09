"""Operate a separate HTTPS demo gateway; owners and localhost stay untouched."""
import argparse
from datetime import datetime
import http.client
import json
import os
from pathlib import Path
import ssl
import subprocess
import time
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.persistence.state import LocalState


def credentials(root, references):
    state=LocalState.snapshot(root)
    original=[reference for reference in references if reference!='LAUNCH_GATEWAY_TOKEN']
    values=CredentialVault(root/'credentials.dpapi',state['deployment_id']).load().environment(original)
    if 'LAUNCH_GATEWAY_TOKEN' in references:
        from amphora_deployment.campaign_launch.credentials import launch_credential
        values.update(launch_credential(root,state['deployment_id']).environment(['LAUNCH_GATEWAY_TOKEN']))
    return values


def invite(root, session):
    config=json.loads((session/'gateway.json').read_bytes())
    listener=config['listener']; key=credentials(root,['GATEWAY_SESSION_KEY'])['GATEWAY_SESSION_KEY']
    tls=ssl.create_default_context(cafile=str(session/'amphora-demo-ca.pem'))
    connection=http.client.HTTPSConnection(listener['address'],57013,context=tls,timeout=10)
    try:
        connection.request('POST','/launcher/ticket',headers={'Authorization':'Bearer '+key})
        response=connection.getresponse();assert response.status==200,'LAN gateway unavailable'
        ticket=json.loads(response.read(4096))['ticket']
        assert type(ticket) is str and all(c.isalnum() or c in '_-' for c in ticket)
    finally:connection.close()
    url='https://'+listener['address']+':57013/#view=question&launch='+ticket
    # Short-lived invitation is deliberately separate from durable evidence/logs.
    (session/'Open Amphora.url').write_text('[InternetShortcut]\nURL='+url+'\n',encoding='utf-8')
    subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',
                    '$inviteText = [Console]::In.ReadToEnd(); Set-Clipboard -Value $inviteText'],
                   input=url,text=True,check=True,capture_output=True)
    print('Five-minute, single-use invitation copied to clipboard and Open Amphora.url.',flush=True)


def serve(args):
    session=args.session.absolute();session.mkdir(parents=True,exist_ok=False)
    config=json.loads(args.baseline.read_bytes());config['profile']='lan-gateway-v1'
    config['listener']={'address':args.address,'subnet':args.subnet,
        'certificate':str((args.tls/'server.pem').absolute()),'private_key':str((args.tls/'server.key').absolute())}
    (session/'gateway.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    for name in ('amphora-demo-ca.pem','amphora-demo-ca.cer'):
        (session/name).write_bytes((args.tls/name).read_bytes())
    references=['GATEWAY_SESSION_KEY']+[peer['token_env'].removeprefix('AMPHORA_') for peer in config['peers'].values()]
    env={k:v for k,v in os.environ.items() if not k.startswith('AMPHORA_')}
    env.update({'AMPHORA_'+key:value for key,value in credentials(args.root,references).items()})
    origin='https://'+args.address+':57013'
    with (session/'gateway.log').open('wb') as log:
        process=subprocess.Popen([str(args.python),'-I','-m','amphora_local_gateway','serve',
                                  '--config',str(session/'gateway.json'),'--port','57013','--stop-file',str(session/'gateway.stop')],
                                 env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        try:
            tls=ssl.create_default_context(cafile=str(session/'amphora-demo-ca.pem'))
            for attempt in range(40):
                assert process.poll() is None,'LAN gateway exited; inspect gateway.log'
                connection=http.client.HTTPSConnection(args.address,57013,context=tls,timeout=2)
                try:
                    connection.request('GET','/session');response=connection.getresponse()
                    assert response.status==401;response.read();break
                except OSError:time.sleep(.25)
                finally:connection.close()
            else:raise RuntimeError('LAN gateway startup timeout')
            record={'status':'ready','origin':origin,'run_id':config['context']['run_id'],
                'scope':config['context']['scope'],'timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'pid':process.pid,'provider_calls':0,'owner_changes':False,'remote_acceptance':'pending'}
            (session/'ready.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
            (session/'browser-input.json').write_text(json.dumps(record),encoding='utf-8')
            print('LAN gateway ready: '+origin,flush=True)
            deadline=time.monotonic()+args.duration
            while time.monotonic()<deadline and not (session/'STOP').exists():
                assert process.poll() is None,'LAN gateway stopped';time.sleep(.5)
        finally:
            # Drain the separate gateway without stopping any scientific service.
            if process.poll() is None:
                (session/'gateway.stop').touch();process.wait(timeout=45)
            (session/'stopped.json').write_text(json.dumps({'timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['serve','invite'])
    for name in ('root','session'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('baseline','tls','python'):parser.add_argument('--'+name,type=Path)
    parser.add_argument('--address',default='192.168.1.70');parser.add_argument('--subnet',default='192.168.1.0/24')
    parser.add_argument('--duration',type=int,default=86400)
    args=parser.parse_args()
    if args.action=='invite':invite(args.root,args.session)
    else:
        assert args.baseline and args.tls and args.python and 1<=args.duration<=86400
        serve(args)
