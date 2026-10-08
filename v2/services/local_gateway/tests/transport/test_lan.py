from dataclasses import replace
import http.client
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import socket
import sys

import pytest
from amphora_local_gateway.configuration import Configuration,GatewayError
from amphora_local_gateway.listener import Listener
from amphora_local_gateway.server import GatewayServer
from amphora_local_gateway.sessions import Sessions,SessionDenied
from test_http import configuration,running

def test_cli_stop_marker_drains_independent_gateway(tmp_path):
    configuration(tmp_path,18000)
    record={'profile':'local-gateway-v1','public_directory':str(tmp_path),
        'peers':{'runtime':{'endpoint':'http://127.0.0.1:18000','token_env':'AMPHORA_RUNTIME_TOKEN'}},
        'context':{'actor_id':'operator','scope':{'tenant_id':'demo','project_id':'demo'},'run_id':None,'synthetic':True},
        'launcher_key_env':'AMPHORA_GATEWAY_SESSION_KEY'}
    path=tmp_path/'config.json';path.write_text(json.dumps(record))
    stop=tmp_path/'STOP';stop.touch()
    with socket.socket() as available:
        available.bind(('127.0.0.1',0));port=available.getsockname()[1]
    result=subprocess.run([sys.executable,'-I','-m','amphora_local_gateway','serve','--config',str(path),
        '--port',str(port),'--stop-file',str(stop)],env={**os.environ,'AMPHORA_RUNTIME_TOKEN':'x'*40,
        'AMPHORA_GATEWAY_SESSION_KEY':'y'*40},capture_output=True,timeout=10)
    assert result.returncode==0,result.stdout

def test_lan_profile_is_explicit_private_scoped_and_preserves_loopback_peers(tmp_path):
    cert=tmp_path/'cert.pem';key=tmp_path/'key.pem';cert.write_text('test');key.write_text('test')
    value={'address':'192.168.1.70','subnet':'192.168.1.0/24','certificate':str(cert),'private_key':str(key)}
    listener=Listener.load(value)
    assert listener.allows('192.168.1.25') and not listener.allows('192.168.2.25')
    assert not listener.allows('127.0.0.1') and not listener.allows('garbage')
    assert listener.origin(57013)=='https://192.168.1.70:57013'
    for update in [{'address':'0.0.0.0'},{'address':'8.8.8.8'},{'subnet':'0.0.0.0/0'},{'address':'192.168.1.255'},{'subnet':'192.168.2.0/24'},{'certificate':'relative.pem'},{'extra':True}]:
        with pytest.raises((GatewayError,ValueError)):Listener.load({**value,**update})
    record={'profile':'lan-gateway-v1','listener':value,'public_directory':str(tmp_path),'peers':{'runtime':{'endpoint':'http://127.0.0.1:18000','token_env':'AMPHORA_RUNTIME_TOKEN'}},'context':{'actor_id':'operator','scope':{'tenant_id':'demo','project_id':'demo'},'run_id':None,'synthetic':True},'launcher_key_env':'AMPHORA_GATEWAY_SESSION_KEY'}
    path=tmp_path/'config.json';path.write_text(json.dumps(record));env={'AMPHORA_RUNTIME_TOKEN':'x'*40,'AMPHORA_GATEWAY_SESSION_KEY':'y'*40}
    assert Configuration.load(path,env).listener==listener
    record['peers']['runtime']['endpoint']='http://192.168.1.70:18000';path.write_text(json.dumps(record))
    with pytest.raises(GatewayError):Configuration.load(path,env)

def test_lan_tickets_expire_and_remain_single_use():
    now=[0];sessions=Sessions(clock=lambda:now[0],ticket_lifetime=300)
    ticket=sessions.issue_ticket();now[0]=299;sessions.exchange(ticket)
    with pytest.raises(SessionDenied):sessions.exchange(ticket)
    ticket=sessions.issue_ticket();now[0]=600
    with pytest.raises(SessionDenied):sessions.exchange(ticket)

def test_actual_tls_origin_cookie_and_ticket_exchange(tmp_path):
    openssl=shutil.which('openssl') or 'C:/Program Files/Git/usr/bin/openssl.exe'
    cert=tmp_path/'cert.pem';key=tmp_path/'key.pem'
    subprocess.run([openssl,'req','-x509','-newkey','rsa:2048','-nodes','-days','1','-keyout',str(key),'-out',str(cert),'-subj','/CN=Gateway test','-addext','subjectAltName=IP:127.0.0.1'],check=True,capture_output=True)
    config=replace(configuration(tmp_path,18000),listener=Listener('127.0.0.1','127.0.0.0/8',cert,key))
    # configuration() creates only public assets; certificate/private key stay local.
    with running(GatewayServer(config,0)) as server:
        tls=ssl.create_default_context(cafile=str(cert))
        def request(path,method='GET',headers=None,body=None):
            connection=http.client.HTTPSConnection('127.0.0.1',server.server_port,context=tls,timeout=5)
            try:
                connection.request(method,path,body=body,headers=headers or {});response=connection.getresponse()
                return response.status,dict(response.getheaders()),response.read()
            finally:connection.close()
        assert request('/')[0]==200
        assert request('/session')[0]==401
        assert request('/',headers={'Host':'attacker.invalid'})[0]==400
        status,_,raw=request('/launcher/ticket','POST',{'Authorization':'Bearer '+config.launcher_key});assert status==200
        body=json.dumps({'ticket':json.loads(raw)['ticket']})
        assert request('/session','POST',{'Origin':'http://127.0.0.1:'+str(server.server_port),'Content-Type':'application/json'},body)[0]==403
        status,headers,_=request('/session','POST',{'Origin':server.origin,'Content-Type':'application/json'},body)
        assert status==200 and '; Secure' in headers['Set-Cookie'] and 'HttpOnly' in headers['Set-Cookie']
        assert request('/session','POST',{'Origin':server.origin,'Content-Type':'application/json'},body)[0]==401
        cookie=headers['Set-Cookie'].split(';')[0]
        assert request('/session',headers={'Cookie':cookie})[0]==200
        assert request('/session/logout','POST',{'Origin':server.origin,'Cookie':cookie})[0]==200
        assert request('/session',headers={'Cookie':cookie})[0]==401
