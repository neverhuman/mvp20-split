"""Test-only process/HTTP harness. No service imports, SQL, or production hooks."""

import json
import os
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


def isolated_env():
    return {k: v for k, v in os.environ.items() if k.upper() in
            {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC"}}


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def request(endpoint, path, token, payload=None, method=None):
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode() if payload is not None else None
    req = Request(endpoint + path, data=body, method=method,
                  headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with build_opener(ProxyHandler({})).open(req, timeout=10) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()


def decoded(*args, **kwargs):
    status, body = request(*args, **kwargs)
    value = json.loads(body)
    assert status == 200, (status, value)
    return value


class Process:
    def __init__(self, python, module, config, env, cwd, port):
        self.child = subprocess.Popen([str(python), "-I", "-m", module, "serve", "--config", str(config),
                                       "--port", str(port)], cwd=cwd, env=env,
                                      stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self.endpoint = f"http://127.0.0.1:{port}"

    def ready(self, token):
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and self.child.poll() is None:
            try:
                if request(self.endpoint, "/ready", token)[0] == 200:
                    return
            except URLError:
                pass
            time.sleep(0.1)
        raise AssertionError("Installed service did not become ready")

    def close(self):
        if self.child.poll() is None:
            self.child.terminate()
        try:
            self.child.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            self.child.kill()
            self.child.communicate(timeout=10)


class ReservationProxy:
    """Forward actual replies; pause a selected response after its durable effect.

    Default is reservation acquisition. Tests can explicitly select claim, completion
    or delivery response windows without changing production entrypoints.
    """
    def __init__(self, endpoint, hold_path="/v1/reservations"):
        self.hold_next = False
        self.arrived = threading.Event()
        self.release = threading.Event()
        self.receipts = []
        self.requests = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                status, response = request(endpoint, self.path,
                    self.headers["Authorization"].removeprefix("Bearer "), body, "POST")
                if self.path == hold_path and status == 200:
                    owner.receipts.append(json.loads(response))
                    owner.requests.append(json.loads(body))
                    if owner.hold_next:
                        owner.hold_next = False
                        owner.arrived.set()
                        owner.release.wait(timeout=8)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                try:
                    self.wfile.write(response)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.endpoint = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
