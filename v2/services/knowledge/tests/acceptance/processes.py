"""Real installed-owner processes; no peer implementation imports in the harness."""

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


class Owner:
    def __init__(self, module, config, environment, token, *, port=None, python=None):
        if port is None:
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
        self.port, self.token = port, token
        self.endpoint = f"http://127.0.0.1:{port}"
        self.process = subprocess.Popen([python or sys.executable, "-I", "-m", module, "serve",
            "--config", str(config), "--port", str(port)], env=environment,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            deadline = time.monotonic() + 15
            while True:
                assert self.process.poll() is None, "Owner exited before readiness"
                try:
                    route = "/ready" if module == "amphora_data_artifacts" else "/health"
                    self.request(route)
                    break
                except urllib.error.URLError:
                    assert time.monotonic() < deadline, "Owner readiness timeout"
                    time.sleep(0.05)
        except BaseException:
            self.stop()
            raise

    def request(self, route, body=None, *, content=None, method=None):
        raw = content if content is not None else None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.endpoint + route, data=raw, method=method,
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    def stop(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=10)


def owned_script(python, script, environment):
    result = subprocess.run([python, "-I", "-c", script], env=environment, capture_output=True, timeout=30)
    assert result.returncode == 0, "Owner-local fixture preparation failed"
