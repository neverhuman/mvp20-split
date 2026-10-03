"""Bounded real CLI-process HTTP fixture; no service-private imports or fixture bypass routes."""

import json
import socket
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: bytes

    def json(self):
        return json.loads(self.body)


class HttpOwner:
    def __init__(self, python, config, environment, token):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            self.port = listener.getsockname()[1]
        self.token = token
        self.process = subprocess.Popen(
            [
                str(python),
                "-I",
                "-m",
                "amphora_data_artifacts",
                "serve",
                "--config",
                str(config),
                "--port",
                str(self.port),
            ],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise RuntimeError("Representation host exited before readiness")
                try:
                    result = self.call("GET", "/ready")
                    if result.status == 200 and result.json()["ready"]:
                        break
                except urllib.error.URLError:
                    pass
                time.sleep(0.05)
            else:
                raise RuntimeError("Representation host readiness deadline exceeded")
        except BaseException:
            self.close()
            raise

    def call(self, method, path, body=None, *, token=None):
        raw = isinstance(body, bytes)
        payload = body if raw or body is None else json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": "Bearer " + (self.token if token is None else token),
            "Content-Type": "application/octet-stream" if raw else "application/json",
        }
        request = urllib.request.Request(
            "http://127.0.0.1:" + str(self.port) + path, data=payload, method=method, headers=headers
        )
        try:
            response = urllib.request.urlopen(request, timeout=15)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            content = response.read(1048577)
            assert len(content) <= 1048576, "Fixture response exceeded bound"
            return HttpResult(response.status, content)

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
