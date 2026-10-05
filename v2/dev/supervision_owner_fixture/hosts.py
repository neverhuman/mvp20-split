"""Owned local processes and a commit-before-reply-loss HTTP fault proxy."""

import http.client
import json
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener


class Owner:
    def __init__(self, python, module, config, env, token, output):
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1', 0))
            port = reservation.getsockname()[1]
        self.endpoint, self.token = f'http://127.0.0.1:{port}', token
        self.log = (output / (module + '.log')).open('ab')
        args = [str(python), '-I', '-m', module]
        if module != 'amphora_agent_planning.supervision_api':
            args.extend(['serve', '--config', str(config)])
        args.extend(['--port', str(port)])
        self.process = subprocess.Popen(args, cwd=output, env=env, stdout=self.log, stderr=self.log,
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            deadline = time.monotonic() + 30
            while True:
                assert self.process.poll() is None, 'Owner exited before ready; inspect local owner log'
                try:
                    self.call('GET', '/ready')
                    break
                except (URLError, TimeoutError):
                    assert time.monotonic() < deadline, 'Owner readiness deadline'
                    time.sleep(.05)
        except BaseException:
            self.close()
            raise

    def call(self, method, path, body=None):
        payload = body if isinstance(body, bytes) else None if body is None else json.dumps(body).encode()
        request = Request(self.endpoint + path, data=payload, method=method,
                          headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
        with build_opener(ProxyHandler({})).open(request, timeout=10) as response:
            raw = response.read(262145)
            assert len(raw) <= 262144
            return json.loads(raw)

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=10)
        self.log.close()


class LostReplyProxy:
    def __init__(self, target, write_path):
        self.target, self.write_path = target, write_path
        self.drop_next, self.dropped, self.records = True, [], []
        state = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                self.forward()

            def do_GET(self):
                self.forward()

            def forward(self):
                parsed = urlsplit(state.target)
                length = int(self.headers.get('Content-Length', '0'))
                assert length <= 262144
                body = self.rfile.read(length) if length else None
                conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=10)
                try:
                    conn.request(self.command, self.path, body, {'Authorization': self.headers.get('Authorization', ''),
                                                               'Content-Type': 'application/json'})
                    response = conn.getresponse()
                    raw = response.read(262145)
                    assert len(raw) <= 262144
                    state.records.append({'method': self.command, 'path': self.path, 'status': response.status})
                    if state.drop_next and self.command == 'POST' and self.path == state.write_path:
                        assert response.status == 200 and json.loads(raw)['outcome']['status'] == 'recorded'
                        state.drop_next = False
                        state.dropped.append(json.loads(raw))
                        self.connection.shutdown(socket.SHUT_RDWR)
                        self.connection.close()
                        return
                    self.send_response(response.status)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)
                finally:
                    conn.close()

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .02}, daemon=True)
        self.thread.start()
        self.endpoint = f'http://127.0.0.1:{self.server.server_port}'

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
