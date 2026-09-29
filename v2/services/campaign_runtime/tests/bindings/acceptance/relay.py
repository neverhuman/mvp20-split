"""Transparent actual Artifact traffic with a response barrier, never owner authority."""

import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class ArtifactRelay:
    def __init__(self, http, endpoint):
        self.events = []
        self.hold_finalize = False
        self.reached, self.release = threading.Event(), threading.Event()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                self.forward()

            def do_POST(self):
                self.forward()

            def do_PUT(self):
                self.forward()

            def forward(self):
                body = self.rfile.read(int(self.headers.get('Content-Length', '0')))
                token = self.headers.get('Authorization', '').removeprefix('Bearer ')
                status, response = http.request(endpoint, self.path, token,
                    body if self.command in {'POST', 'PUT'} else None, self.command)
                event = {'method': self.command, 'path': self.path, 'status': status,
                         'body_sha256': hashlib.sha256(body).hexdigest()}
                if self.command == 'POST':
                    event['command'] = json.loads(body)
                if response and not self.path.endswith('/content'):
                    event['response'] = json.loads(response)
                owner.events.append(event)
                if owner.hold_finalize and self.path == '/v1/artifacts/finalize' and status == 200:
                    owner.hold_finalize = False
                    event['barrier'] = 'actual_finalization_before_runtime_response'
                    owner.reached.set()
                    assert owner.release.wait(30), 'Acceptance controller failed to release response barrier'
                try:
                    self.send_response(status)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(response)))
                    self.end_headers()
                    self.wfile.write(response)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.endpoint = f'http://127.0.0.1:{self.server.server_port}'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)
