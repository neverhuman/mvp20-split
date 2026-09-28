"""Test-owned stdlib process/HTTP helpers; no service or database imports."""

import json
import os
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


def isolated_env():
    return {k: v for k, v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC"}}


def request(endpoint, path, token, payload=None):
    raw = None if payload is None else json.dumps(payload).encode()
    query = Request(endpoint+path, data=raw, headers={"Authorization": "Bearer "+token, "Content-Type": "application/json"})
    try:
        with build_opener(ProxyHandler({})).open(query, timeout=10) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read())


class Process:
    def __init__(self, python, config, env, cwd):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.endpoint = f"http://127.0.0.1:{port}"
        self.child = subprocess.Popen([str(python), "-I", "-m", "amphora_capability_registry", "serve",
            "--config", str(config), "--port", str(port)], cwd=cwd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def ready(self):
        deadline = time.monotonic()+15
        while time.monotonic()<deadline:
            if self.child.poll() is not None:
                raise AssertionError("Installed registry exited: "+self.child.stderr.read().decode()[-1200:])
            try:
                if request(self.endpoint, "/openapi.json", "unused")[0] == 200:
                    return
            except (OSError, URLError):
                time.sleep(0.05)
        raise AssertionError("Registry readiness deadline")

    def close(self):
        if self.child.poll() is None:
            self.child.kill()
        self.child.communicate(timeout=10)
