"""Bounded actual-owner HTTP processes, without service imports or database reads."""
import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request


class Owner:
    def __init__(self, python, module, config, environment, token, *, port=None):
        self.token = token
        if port is None:
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0))
                port = listener.getsockname()[1]
        self.endpoint = f'http://127.0.0.1:{port}'
        self.process = subprocess.Popen([str(python), '-I', '-m', module, 'serve',
            '--config', str(config), '--port', str(port)], env=environment,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            deadline = time.monotonic() + 20
            while True:
                assert self.process.poll() is None, 'Owner failed startup'
                try:
                    self.request('/ready' if module == 'amphora_data_artifacts' else '/health')
                    break
                except urllib.error.URLError:
                    assert time.monotonic() < deadline, 'Owner readiness deadline'
                    time.sleep(.05)
        except BaseException:
            self.close()
            raise

    def request(self, path, body=None, *, content=None, method=None, binary=False, token=None):
        assert path.startswith('/') and not path.startswith('//')
        raw = content if content is not None else None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.endpoint + path, data=raw, method=method,
            headers={'Authorization': 'Bearer ' + (token or self.token), 'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=30) as response:
            value = response.read(4194305)
            assert len(value) <= 4194304, 'Owner response limit'
            return value if binary else json.loads(value)

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=10)


def owned_setup(python, script, environment):
    result = subprocess.run([str(python), '-I', '-c', script], env=environment,
        capture_output=True, timeout=45, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert result.returncode == 0, 'Isolated owner setup failed'


def base_environment():
    return {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
