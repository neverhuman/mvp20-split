"""Real gateway/static assets; explicitly synthetic Runtime HTTP peer for browser tests."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading

from amphora_local_gateway.configuration import Configuration, Peer
from amphora_local_gateway.server import GatewayServer


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--public',type=Path,required=True)
    parser.add_argument('--fixture',type=Path,required=True)
    parser.add_argument('--selected',action='store_true')
    args=parser.parse_args()
    fixture=json.loads(args.fixture.read_bytes())
    token='synthetic-owner-token-not-a-deployment-secret'
    class Owner(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.headers.get('Authorization') != 'Bearer '+token:
                self.send_response(401);self.end_headers();return
            path=self.path.split('?')[0]
            value=fixture['snapshot'] if path.endswith('/nodes') else fixture['detail'] if '/nodes/' in path else fixture['events'] if path.endswith('/invalidations') else None
            if value is None:
                self.send_response(404);self.end_headers();return
            raw=json.dumps(value).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    owner=ThreadingHTTPServer(('127.0.0.1',0),Owner)
    owner_thread=threading.Thread(target=owner.serve_forever,daemon=True);owner_thread.start()
    context={'actor_id':'operator','scope':fixture['scope'],'run_id':fixture['run'] if args.selected else None,'synthetic':True}
    gateway=GatewayServer(Configuration(args.public,{'runtime':Peer(owner.server_port,token)},context,os.environ['GATEWAY_FIXTURE_KEY']),0)
    print(json.dumps({'url':gateway.origin}),flush=True)
    try:gateway.serve_forever(poll_interval=.1)
    finally:gateway.server_close();owner.shutdown();owner.server_close();owner_thread.join(timeout=5)


if __name__=='__main__':main()
