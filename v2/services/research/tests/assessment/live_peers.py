"""Research-owned actual peer harness; subprocesses import only their owning implementation."""

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


class Owner:
    def __init__(self, module, config, environment, token, python=None, *, port=None):
        if port is None:
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
        self.endpoint, self.token = f"http://127.0.0.1:{port}", token
        self.process = subprocess.Popen([python or sys.executable, "-I", "-m", module, "serve", "--config",
            str(config), "--port", str(port)], env=environment, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            deadline = time.monotonic() + 15
            while True:
                assert self.process.poll() is None, "Peer exited before readiness"
                try:
                    self.request("/ready" if module == "amphora_data_artifacts" else "/health")
                    break
                except urllib.error.URLError:
                    assert time.monotonic() < deadline, "Peer readiness timeout"
                    time.sleep(0.05)
        except BaseException:
            self.stop()
            raise

    def request(self, route, value=None, *, content=None, method=None):
        raw = content if content is not None else None if value is None else json.dumps(value).encode()
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
    assert result.returncode == 0, "Peer-owned fixture setup failed"
