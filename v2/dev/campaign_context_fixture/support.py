"""Test-owned process and bounded public HTTP helpers, no service imports."""

import json
import os
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


def environment():
    result = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    return dict(result, PYTHONUTF8='1')


class Owner:
    def __init__(self, python, module, config, env, token, output):
        assert module in {'amphora_capability_registry', 'amphora_campaign_runtime', 'amphora_data_artifacts', 'amphora_knowledge'}
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        self.endpoint, self.token = f'http://127.0.0.1:{port}', token
        self.log = (output / (module + '.log')).open('ab')
        self.process = subprocess.Popen([str(python), '-I', '-m', module, 'serve', '--config', str(config), '--port', str(port)],
            env=env, cwd=output, stdout=self.log, stderr=self.log, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                assert self.process.poll() is None, module + ' exited; inspect owner log'
                try:
                    self.call('GET', '/health' if module == 'amphora_knowledge' else '/ready' if module == 'amphora_data_artifacts' else '/openapi.json')
                    return
                except (URLError, TimeoutError):
                    time.sleep(0.05)
            raise RuntimeError(module + ' readiness deadline')
        except BaseException:
            self.close()
            raise

    def call(self, method, path, body=None):
        payload = body if isinstance(body, bytes) else None if body is None else json.dumps(body).encode()
        req = Request(self.endpoint + path, payload, method=method,
            headers={'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
        try:
            with build_opener(ProxyHandler({})).open(req, timeout=20) as response:
                raw = response.read(4194305)
                assert len(raw) <= 4194304
                return json.loads(raw)
        except HTTPError as error:
            raise RuntimeError(f'Fixture HTTP {method} {path}: {error.code}') from None

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=10)
        self.log.close()


def run(python, script, args, env, output):
    result = subprocess.run([str(python), '-I', str(script), *map(str, args)], env=env, cwd=output,
        capture_output=True, text=True, encoding='utf-8', timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    with (output / 'processes.log').open('a', encoding='utf-8') as stream:
        stream.write(result.stdout + result.stderr)
    assert result.returncode == 0, 'Fixture process failed; inspect processes.log'
    return json.loads(result.stdout)
