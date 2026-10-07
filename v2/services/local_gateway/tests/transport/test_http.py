from contextlib import contextmanager
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading

from amphora_local_gateway.configuration import Configuration, Peer
from amphora_local_gateway.server import GatewayServer
from amphora_local_gateway.__main__ import launch


@contextmanager
def running(server):
    thread = threading.Thread(target=lambda:server.serve_forever(poll_interval=.05))
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive()


def request(server, path, *, method='GET', headers=None, body=None):
    connection = http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
    try:
        connection.request(method,path,body=body,headers=headers or {})
        response=connection.getresponse()
        return response.status,dict(response.getheaders()),response.read()
    finally:
        connection.close()


class Owner(BaseHTTPRequestHandler):
    def log_message(self,*args):pass

    def do_GET(self):
        self.server.seen.append(dict(self.headers))
        if self.path.endswith('/redirect'):
            self.send_response(302);self.send_header('Location','http://remote.invalid/');self.end_headers();return
        if self.path.endswith('/oversized'):
            self.send_response(200);self.send_header('Content-Length',str(8388609));self.end_headers();return
        code=403 if self.path.endswith('/denied') else 200
        raw=b'private owner error and token' if code==403 else b'{"status":"actual-owner-fixture"}'
        self.send_response(code)
        self.send_header('Content-Type','text/html' if self.path.endswith('/active-content') else 'application/json')
        self.send_header('Content-Length',str(len(raw)))
        self.send_header('Set-Cookie','owner_secret=must-not-forward')
        self.end_headers();self.wfile.write(raw)


def configuration(tmp_path, peer_port):
    for name in ['index.html','app.js','app.css']:(tmp_path/name).write_text('fixture-'+name)
    return Configuration(tmp_path,{'runtime':Peer(peer_port,'owner-private-token-123456789012345')},
        {'actor_id':'operator','scope':{'tenant_id':'demo','project_id':'demo'},'run_id':None,'synthetic':True},
        'launcher-private-token-1234567890123')


def login(server):
    status,_,raw=request(server,'/launcher/ticket',method='POST',headers={'Authorization':'Bearer '+server.configuration.launcher_key})
    assert status==200
    ticket=json.loads(raw)['ticket']
    status,headers,body=request(server,'/session',method='POST',headers={'Origin':server.origin,'Content-Type':'application/json'},body=json.dumps({'ticket':ticket}))
    assert status==200
    assert 'HttpOnly' in headers['Set-Cookie'] and 'SameSite=Strict' in headers['Set-Cookie']
    return headers['Set-Cookie'].split(';')[0],ticket


def test_actual_gateway_sessions_scope_and_byte_preserving_proxy(tmp_path):
    owner=ThreadingHTTPServer(('127.0.0.1',0),Owner);owner.seen=[]
    with running(owner),running(GatewayServer(configuration(tmp_path,owner.server_port),0)) as gateway:
        assert request(gateway,'/')[0]==200
        assert request(gateway,'/api/runtime/v1/runs')[0]==401
        assert not owner.seen
        cookie,ticket=login(gateway)
        headers={'Cookie':cookie,'Authorization':'Bearer browser-must-not-control-owner'}
        status,response,raw=request(gateway,'/api/runtime/v1/runs',headers=headers)
        assert status==200 and raw==b'{"status":"actual-owner-fixture"}'
        assert 'Set-Cookie' not in response
        assert owner.seen[-1]['Authorization']=='Bearer owner-private-token-123456789012345'
        assert 'Cookie' not in owner.seen[-1]
        status,response,raw=request(gateway,'/api/runtime/v1/active-content',headers=headers)
        assert status==200 and response['Content-Type']=='application/octet-stream'
        assert request(gateway,'/api/runtime/v1/redirect',headers=headers)[0]==502
        assert request(gateway,'/api/runtime/v1/oversized',headers=headers)[0]==502
        status,_,raw=request(gateway,'/api/runtime/v1/denied',headers=headers)
        assert status==403 and b'private' not in raw
        status,_,_=request(gateway,'/session',method='POST',headers={'Origin':gateway.origin,'Content-Type':'application/json'},body=json.dumps({'ticket':ticket}))
        assert status==401
        assert request(gateway,'/session/logout',method='POST',headers={'Cookie':cookie,'Origin':gateway.origin})[0]==200
        assert request(gateway,'/session',headers={'Cookie':cookie})[0]==401


def test_origin_host_and_body_fail_before_owner_request(tmp_path):
    owner=ThreadingHTTPServer(('127.0.0.1',0),Owner);owner.seen=[]
    with running(owner),running(GatewayServer(configuration(tmp_path,owner.server_port),0)) as gateway:
        cookie,_=login(gateway)
        assert request(gateway,'/',headers={'Host':'attacker.invalid'})[0]==400
        assert request(gateway,'/api/runtime/v1/commands',method='POST',headers={'Cookie':cookie,'Origin':'http://attacker.invalid'})[0]==403
        assert request(gateway,'/api/runtime/v1/commands',method='POST',headers={'Cookie':cookie})[0]==403
        assert not owner.seen
        assert request(gateway,'/launcher/ticket',method='POST')[0]==403


def test_launcher_opens_only_a_one_time_fragment_ticket(tmp_path,monkeypatch):
    opened=[]
    monkeypatch.setattr('webbrowser.open',lambda url:opened.append(url) or True)
    with running(GatewayServer(configuration(tmp_path,19999),0)) as gateway:
        launch(gateway.origin,'AMPHORA_KEY',{'AMPHORA_KEY':gateway.configuration.launcher_key})
        assert len(opened)==1 and opened[0].startswith(gateway.origin+'/#launch=')
        assert gateway.configuration.launcher_key not in opened[0]
        ticket=opened[0].split('#launch=')[1]
        gateway.sessions.authenticate(gateway.sessions.exchange(ticket))
