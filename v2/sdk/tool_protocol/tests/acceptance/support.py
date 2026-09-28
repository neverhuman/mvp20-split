"""Test-owned processes and transparent fault relay; no owner imports or SQL."""

import hashlib
import http.client
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
    return {key: value for key, value in os.environ.items()
            if key.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC"}}


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def request(endpoint, path, token, payload=None, method=None):
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode() if payload is not None else None
    command = Request(endpoint + path, data=body, method=method,
                      headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    try:
        with build_opener(ProxyHandler({})).open(command, timeout=15) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()


def decoded(*args, **kwargs):
    status, body = request(*args, **kwargs)
    assert status == 200, "Public owner request failed: " + str(status)
    return json.loads(body)


class Service:
    def __init__(self, python, module, config, env, directory, port):
        self.python, self.module, self.config = str(python), module, str(config)
        self.env, self.directory, self.port = env, directory, port
        self.endpoint = f"http://127.0.0.1:{port}"
        self.log = (directory / (module + "-" + str(port) + ".log")).open("wb")
        self.child = subprocess.Popen([self.python, "-I", "-m", module, "serve", "--config", self.config,
            "--port", str(port)], cwd=directory, env=env, stdout=subprocess.DEVNULL, stderr=self.log)

    def ready(self, token):
        deadline = time.monotonic() + 30
        while self.child.poll() is None and time.monotonic() < deadline:
            try:
                if request(self.endpoint, "/ready", token)[0] == 200:
                    return
            except URLError:
                pass
            time.sleep(0.1)
        raise AssertionError("Independent service did not become ready")

    def close(self):
        if self.child.poll() is None:
            self.child.terminate()
        try:
            self.child.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            self.child.kill()
            self.child.communicate(timeout=10)
        self.log.close()


class FaultRelay:
    """Forward real owner operations; selected fault changes only transport delivery."""

    def __init__(self, endpoint):
        self.drop_path = None
        self.interrupt_stream = False
        self.events = []
        self.lock = threading.Lock()
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
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                token = self.headers.get("Authorization", "").removeprefix("Bearer ")
                event = {"method": self.command, "path": self.path, "body_sha256": hashlib.sha256(body).hexdigest()}
                if self.command == "POST":
                    event["identity"] = json.loads(body).get("identity")
                with owner.lock:
                    interrupt = owner.interrupt_stream and self.command == "PUT"
                    owner.interrupt_stream = owner.interrupt_stream and not interrupt
                    drop = owner.drop_path == self.path and self.command == "POST"
                    if drop:
                        owner.drop_path = None
                if interrupt:
                    address = endpoint.removeprefix("http://")
                    connection = http.client.HTTPConnection(address, timeout=5)
                    try:
                        connection.putrequest("PUT", self.path)
                        connection.putheader("Authorization", "Bearer " + token)
                        connection.putheader("Content-Length", str(len(body)))
                        connection.endheaders()
                        connection.send(body[:max(1, len(body) // 2)])
                    finally:
                        connection.close()
                    status, response = 503, b'{"reason_code":"test_stream_interrupted"}'
                    event["fault"] = "partial_body_disconnect"
                else:
                    try:
                        status, response = request(endpoint, self.path, token,
                            body if self.command in {"POST", "PUT"} else None, self.command)
                    except (URLError, OSError, http.client.HTTPException) as error:
                        status, response = 503, b'{"reason_code":"relay_upstream_unavailable"}'
                        event["upstream_failure"] = type(error).__name__
                event["status"] = status
                if drop:
                    assert status == 200, "Fault barrier requires a successful actual owner operation"
                    event["fault"] = "response_dropped_after_owner_success"
                with owner.lock:
                    owner.events.append(event)
                if drop:
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                try:
                    self.wfile.write(response)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.endpoint = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)
