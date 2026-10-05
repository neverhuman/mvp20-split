"""Exercise the configured CLI as a real, separately running local HTTP host."""

import json
import os
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener

import pytest

from ..supervision_intake.support import command, request
from .test_http import TOKEN


def environment(principal):
    env = os.environ.copy()
    env['PYTHONUTF8'] = '1'
    env['AMPHORA_PLANNING_SUPERVISION_CREDENTIALS'] = json.dumps([{
        'token': TOKEN, 'actor_id': principal.actor_id,
        'scope': principal.scope.model_dump(), 'actions': sorted(principal.actions),
    }])
    return env


def test_configured_cli_records_and_recovers_over_real_http(stored, tmp_path):
    env = environment(stored.principal)
    env['AMPHORA_PLANNING_DATABASE_URL'] = stored.engine.url.render_as_string(hide_password=False)
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    opener = build_opener(ProxyHandler({}))
    base = f'http://127.0.0.1:{port}'
    with (tmp_path / 'host.log').open('wb') as log:
        process = subprocess.Popen([sys.executable, '-m', 'amphora_agent_planning.supervision_api',
                                    '--port', str(port)], env=env, stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 15
            while True:
                assert process.poll() is None, 'Planning host exited before readiness; logs retained locally'
                try:
                    with opener.open(base + '/ready', timeout=1) as response:
                        assert json.load(response)['mode'] == 'supervisor_intake_only'
                    break
                except URLError:
                    assert time.monotonic() < deadline, 'Planning host did not become ready'
                    time.sleep(.05)
            incoming = command(request(stored.principal))
            headers = {'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'}
            with opener.open(Request(base + '/v1/supervision/requests', data=incoming.canonical_bytes,
                                     headers=headers), timeout=5) as response:
                first = response.read()
            with opener.open(Request(base + '/v1/supervision/receipts/query', data=incoming.canonical_bytes,
                                     headers=headers), timeout=5) as response:
                assert response.read() == first
            assert json.loads(first)['outcome']['status'] == 'recorded'
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


@pytest.mark.parametrize('mode', ['missing', 'invalid-url', 'port'])
def test_cli_rejects_bad_configuration_without_secret_echo(stored, mode):
    env = environment(stored.principal)
    env.pop('AMPHORA_PLANNING_DATABASE_URL', None)
    args = []
    if mode == 'invalid-url':
        env['AMPHORA_PLANNING_DATABASE_URL'] = 'secret-invalid-database-address'
    if mode == 'port':
        args = ['--port', '0']
    result = subprocess.run([sys.executable, '-m', 'amphora_agent_planning.supervision_api', *args],
                            env=env, capture_output=True, timeout=15, check=False)
    assert result.returncode != 0
    assert b'Traceback' not in result.stderr and b'secret-invalid' not in result.stderr
    assert TOKEN.encode() not in result.stderr
