"""Scripted Runtime over real loopback HTTP; never an actual Runtime owner claim."""

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from amphora_agent_planning.supervision_client import RuntimeClient
from amphora_contracts_supervision import SupervisionResponse, parse_supervision_command

from ..supervision_client.support import receipt

TOKEN = 'synthetic-capture-runtime-token-00000000000000'


class RuntimePeer:
    def __init__(self, principal):
        self.command = self.payload = self.owner_receipt = None
        self.calls = []
        self.drop_write = self.readback_down = self.disappear = False
        self.outcome = 'recorded'
        peer = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                raw = self.rfile.read(int(self.headers['Content-Length']))
                peer.calls.append(('POST', self.path, raw))
                assert self.headers['Authorization'] == 'Bearer ' + TOKEN
                if self.path.endswith('/receipts/query'):
                    if peer.command is None or peer.disappear:
                        return self.send(404)
                    assert raw == peer.command.canonical_bytes
                    return self.send(200, peer.owner_receipt)
                assert self.path == '/v1/supervision/responses'
                command = parse_supervision_command('runtime.supervision.respond', raw)
                assert peer.command is None or command == peer.command
                peer.command = command
                peer.payload = SupervisionResponse.model_validate_json(json.dumps(json.loads(raw)['payload']))
                peer.owner_receipt = receipt(command, peer.payload, peer.outcome)
                if peer.drop_write:
                    peer.drop_write = False
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                self.send(200, peer.owner_receipt)

            def do_GET(self):
                peer.calls.append(('GET', self.path, None))
                assert self.headers['Authorization'] == 'Bearer ' + TOKEN
                if peer.readback_down:
                    return self.send(503)
                assert self.path == '/v1/supervision/responses/' + peer.payload.response_id
                self.send(200, peer.payload)

            def send(self, status, value=None):
                raw = b'' if value is None else value.model_dump_json().encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .02}, daemon=True)
        self.client = RuntimeClient(principal.actor_id, principal.scope,
            f'http://127.0.0.1:{self.server.server_port}', TOKEN)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        assert not self.thread.is_alive()
