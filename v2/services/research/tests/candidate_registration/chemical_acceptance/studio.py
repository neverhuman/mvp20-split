"""Installed Gateway and built Studio over actual owners; credentials stay in env."""
import json
from pathlib import Path
import subprocess
import ssl
import time
import urllib.request
import uuid
from datetime import datetime


def verify(e, configuration, report):
    inspect(e,configuration,report,False)
    if configuration.get('lan'):
        inspect(e,configuration,report,True)


def inspect(e, configuration, report, lan):
    root=e.root/('studio-lan' if lan else 'studio')
    root.mkdir()
    key=uuid.uuid4().hex+uuid.uuid4().hex
    hold=configuration.get('hold_seconds',0)
    port=57013 if lan else 57014 if hold else e.public_http.free_port()
    environment=e.public_http.isolated_env()
    environment['AMPHORA_BROWSER_LAUNCH_KEY']=key
    peers={}
    for name,actor in [('runtime','admin'),('artifact','worker1'),('research','admin'),('registry','admin')]:
        variable='AMPHORA_STUDIO_'+name.upper()+'_TOKEN'
        environment[variable]=e.tokens[actor]
        peers[name]={'endpoint':getattr(e,name).endpoint,'token_env':variable}
    config={'profile':'local-gateway-v1','public_directory':configuration['public_directory'],
        'peers':peers,'context':{'actor_id':'admin','scope':e.scope,'run_id':e.active_run,'synthetic':True},
        'launcher_key_env':'AMPHORA_BROWSER_LAUNCH_KEY'}
    if lan:
        config['profile']='lan-gateway-v1'
        config['listener']={key:configuration['lan'][key] for key in ('address','subnet','certificate','private_key')}
        environment['NODE_EXTRA_CA_CERTS']=configuration['lan']['ca']
    path=root/'gateway.json'
    path.write_text(json.dumps(config),encoding='utf-8')
    stop=root/'STOP'
    origin=f"https://{configuration['lan']['address']}:{port}" if lan else f'http://127.0.0.1:{port}'
    tls=ssl.create_default_context(cafile=configuration['lan']['ca']) if lan else None
    with (root/'gateway.log').open('wb') as log:
        process=subprocess.Popen([configuration['gateway_python'],'-I','-m','amphora_local_gateway','serve',
            '--config',str(path),'--port',str(port),'--stop-file',str(stop)],cwd=root,env=environment,
            stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            for _ in range(100):
                if process.poll() is not None:raise RuntimeError('candidate_gateway_exited')
                try:
                    with urllib.request.urlopen(origin,timeout=1,context=tls) as response:
                        if response.status==200:break
                except (OSError,TimeoutError):time.sleep(.1)
            else:raise RuntimeError('candidate_gateway_start_timeout')
            browser_input={'origin':origin,'scope':e.scope,'run_id':e.active_run,
                'candidate':report['candidate'],'completion_id':report['completion']['completion_id']}
            if lan:
                browser_input['tls_certificate']=configuration['lan']['certificate']
            request=root/'browser-input.json';request.write_text(json.dumps(browser_input),encoding='utf-8')
            studio=Path(__file__).absolute().parents[5]/'studio'
            with (root/'browser.log').open('wb') as output:
                result=subprocess.run(['node','tests/integration/candidate_inspector.mjs',str(request),str(root/'browser')],
                    cwd=studio,env=environment,stdout=output,stderr=subprocess.STDOUT,timeout=180,
                    creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode:raise RuntimeError('candidate_actual_browser_failed')
            if hold:
                invite=root/'INVITE';invite.touch()
                deadline=time.monotonic()+hold
                while time.monotonic()<deadline and not stop.exists():
                    if process.poll() is not None:raise RuntimeError('candidate_example_gateway_exited')
                    if invite.exists():
                        request=urllib.request.Request(origin+'/launcher/ticket',method='POST',headers={'Authorization':'Bearer '+key})
                        with urllib.request.urlopen(request,timeout=10) as response:
                            assert response.status==200
                            ticket=json.loads(response.read(4096))['ticket']
                        assert isinstance(ticket,str) and all(c.isalnum() or c in '_-' for c in ticket)
                        (root/'Open supplied structure.url').write_text('[InternetShortcut]\nURL='+origin+'/#view=knowledge&launch='+ticket+'\n',encoding='utf-8')
                        (root/'ready.json').write_text(json.dumps({'status':'ready','origin':origin,
                            'scope':e.scope,'run_id':e.active_run,'candidate':report['candidate']['reference'],
                            'supplied_structure':True,'provider_calls':0,
                            'timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}),encoding='utf-8')
                        invite.unlink()
                    time.sleep(.25)
        finally:
            stop.touch()
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=10)
            (root/'stopped.json').write_text(json.dumps({'status':'drained','timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}),encoding='utf-8')
