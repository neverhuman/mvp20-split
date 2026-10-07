"""Actual installed native turns on an empty synthetic scope; no model or campaign."""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

from amphora_deployment.lifecycle import ProcessJob
from amphora_deployment.lifecycle.configuration import control_token
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState


def verify(output, source_manifest, planning_installation, planning_lock):
    output.mkdir(parents=True, exist_ok=False)
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    routes = Routes.load(root)
    original_state = LocalState.snapshot(root)
    original_vault = (root / 'credentials.dpapi').read_bytes()
    token = control_token(root)
    scope = {'tenant_id': 'internal', 'project_id': 'worker-proof-' + uuid.uuid4().hex}
    source = json.loads(source_manifest.read_bytes())
    owners = {name: dict(source['owners'][name]) for name in ('runtime', 'planning')}
    owners['planning']['installation'] = str(planning_installation)
    owners['planning']['source_lock'] = str(planning_lock)
    owners['runtime']['secret_references'] = list(set(owners['runtime']['secret_references']) |
        {'RUNTIME_ARTIFACT_TOKEN', 'RUNTIME_PLANNING_TOKEN'})
    owners['planning']['secret_references'] = list(set(owners['planning']['secret_references']) |
        {'PLANNING_DATA_TOKEN', 'PLANNING_RUNTIME_TOKEN'})

    def write(name, record):
        path = output / name
        path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        return path

    manifest = write('owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    def peer(owner, token_name):
        return {'endpoint': routes.endpoint(owner), 'token_env': 'AMPHORA_' + token_name}
    runtime_config = {'database_url_env': 'AMPHORA_RUNTIME_DATABASE_URL', 'actor_id': 'worker-proof', 'scope': scope,
        'planning': peer('planning', 'RUNTIME_PLANNING_TOKEN') | {'actor_id': 'worker-proof'},
        'data': peer('artifact', 'RUNTIME_ARTIFACT_TOKEN') | {'actor_id': 'worker-proof'}}
    planning_config = {'database_url_env': 'AMPHORA_PLANNING_DATABASE_URL', 'actor_id': 'worker-proof', 'scope': scope,
        'publisher_id': 'worker-proof', 'data': peer('artifact', 'PLANNING_DATA_TOKEN'),
        'runtime': peer('runtime', 'PLANNING_RUNTIME_TOKEN'), 'templates': [], 'provider': 'disabled'}
    workers = {}
    for name, config in (('runtime', runtime_config), ('planning', planning_config)):
        workers[name + '-checkpoint'] = {'configuration': str(write(name + '-worker.json', config)),
                                         'source_lock': owners[name]['source_lock'], 'scope': None}
    sidecar = write('workers.json', {'profile': 'local-native-workers-v1', 'workers': workers})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def control(path, method='GET', expected=200):
        request = urllib.request.Request(routes.endpoint('supervisor') + path, method=method,
                                         headers={'Authorization': 'Bearer ' + token})
        try:
            response = opener.open(request, timeout=30)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = json.loads(response.read(65537))
            assert response.status == expected, 'Unexpected control status'
            return raw

    evidence = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'scope': scope,
                'controller_python': sys.executable, 'model_calls': 0, 'campaigns_admitted': 0}
    # No provider environment reaches this proof, even if configured in the shell.
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    with ProcessJob() as job:
        process = subprocess.Popen([sys.executable, '-I', '-m', 'amphora_deployment.lifecycle', 'serve',
            '--root', str(root), '--manifest', str(manifest), '--workers-manifest', str(sidecar)], env=environment,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        job.attach(process)
        try:
            deadline = time.monotonic() + 60
            while True:
                try:
                    control('/status')
                    break
                except OSError:
                    assert process.poll() is None and time.monotonic() < deadline, 'Controller startup failed'
                    time.sleep(.2)
            for owner in owners:
                control('/owners/' + owner + '/start', 'POST')
            for name in workers:
                control('/workers/' + name + '/start', 'POST')
            blocked = control('/owners/runtime/drain', 'POST', 409)
            assert blocked['error'] == 'worker_requires_quiescence'
            deadline = time.monotonic() + 90
            while True:
                report = control('/status')['workers']
                assert all(not item['faulted'] for item in report.values()), 'Native owner turn failed'
                if all(item['completed_turns'] >= 1 for item in report.values()):
                    break
                assert time.monotonic() < deadline, 'Native turns did not complete'
                time.sleep(.2)
            evidence['completed_before_quiesce'] = report
            evidence['quiesce_requested'] = {
                name: control('/workers/' + name + '/quiesce', 'POST') for name in workers}
            deadline = time.monotonic() + 60
            while True:
                report = control('/status')['workers']
                if all(item['state'] == 'quiescent' for item in report.values()):
                    break
                assert time.monotonic() < deadline and all(not item['faulted'] for item in report.values())
                time.sleep(.2)
            evidence['quiescent'] = report
            for owner in owners:
                control('/owners/' + owner + '/drain', 'POST')
            deadline = time.monotonic() + 60
            while True:
                status = control('/status')
                if all(item['state'] == 'exited' for item in status['owners'].values()):
                    break
                assert time.monotonic() < deadline
                time.sleep(.2)
            assert all(item['exit_code'] == 0 for item in status['owners'].values())
            assert status['workers'] == report, 'Quiesced workers launched more work'
            control('/shutdown', 'POST')
            assert process.wait(timeout=15) == 0
            evidence['owners_drained'] = status['owners']
        finally:
            job.close()
            process.wait(timeout=15)
    assert LocalState.snapshot(root) == original_state and (root / 'credentials.dpapi').read_bytes() == original_vault
    evidence.update(status='passed', early_api_drain_rejected=True, installation_state_unchanged=True,
        limits=['Actual installed Runtime/Planning empty-scope database sweeps and API drain only',
                'No active campaign, provider call, scientific container or tool eligibility proof'])
    write('evidence.json', evidence)
    print(json.dumps({'status': 'passed', 'workers': len(workers), 'model_calls': 0}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-manifest', type=Path, required=True)
    parser.add_argument('--planning-installation', type=Path, required=True)
    parser.add_argument('--planning-lock', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output.absolute(), args.source_manifest.absolute(),
           args.planning_installation.absolute(), args.planning_lock.absolute())
