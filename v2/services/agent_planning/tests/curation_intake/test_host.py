"""Actual configured host replacement recovers original curation without dispatch."""
import json
import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener

from .support import environment


@contextmanager
def host(env, path):
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    opener = build_opener(ProxyHandler({}))
    base = f'http://127.0.0.1:{port}'
    with path.open('wb') as log:
        process = subprocess.Popen([sys.executable, '-m', 'amphora_agent_planning.supervision_api',
                                    '--port', str(port)], env=env, stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 20
            while True:
                assert process.poll() is None, 'Owned curation host failed; local log retained'
                try:
                    with opener.open(base + '/ready', timeout=1) as response:
                        assert json.load(response)['mode'] == 'supervisor_intake_and_curation'
                    break
                except URLError:
                    assert time.monotonic() < deadline
                    time.sleep(.05)
            yield base, opener
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def test_original_curation_recovers_after_actual_process_replacement(stored, tmp_path):
    principal, raw, _journal = environment(stored)
    env = os.environ.copy()
    token = 'curation-host-fixture-token-000000000000000000'
    env.update(PYTHONUTF8='1', AMPHORA_PLANNING_CURATION_POLICIES='["synthetic"]',
               AMPHORA_PLANNING_DATABASE_URL=stored.engine.url.render_as_string(hide_password=False),
               AMPHORA_PLANNING_SUPERVISION_CREDENTIALS=json.dumps([{
                   'token': token, 'actor_id': principal.actor_id,
                   'scope': principal.scope.model_dump(mode='json'), 'actions': sorted(principal.actions)}]))
    env.pop('AMPHORA_PLANNING_TOPOLOGY_CONFIG', None)
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
    with host(env, tmp_path / 'first.log') as (base, opener):
        with opener.open(Request(base + '/v1/campaign-curations', data=raw.encode(), headers=headers), timeout=5) as response:
            original = response.read()
    receipt = json.loads(original)
    env['AMPHORA_PLANNING_CURATION_POLICIES'] = '[]'
    credential = json.loads(env['AMPHORA_PLANNING_SUPERVISION_CREDENTIALS'])
    credential[0]['actions'] = ['read_curations']
    env['AMPHORA_PLANNING_SUPERVISION_CREDENTIALS'] = json.dumps(credential)
    query = json.dumps({'identity': receipt['identity'], 'request_sha256': receipt['request_sha256']}).encode()
    with host(env, tmp_path / 'replacement.log') as (base, opener):
        with opener.open(Request(base + '/v1/campaign-curations/receipts/query', data=query, headers=headers), timeout=5) as response:
            assert response.read() == original
        with opener.open(Request(base + '/v1/campaign-curations/' + receipt['reference']['curation_id'], headers=headers), timeout=5) as response:
            view = json.load(response)
            assert view['receipt'] == receipt and view['provider'] is None
