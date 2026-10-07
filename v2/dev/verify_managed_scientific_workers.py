"""Actual local controller/TLS/Runtime/Data/tool denial and nonblocking quiescence proof."""

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from contextlib import ExitStack
from datetime import datetime
from pathlib import Path

from amphora_deployment.lifecycle import ProcessJob
from amphora_deployment.lifecycle.configuration import control_token
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.scientific_workers.ownership import require_released, retained_turns
from amphora_deployment.tool_access import TLSIdentity

IMAGE = 'sha256:7538bece7dceb2f6c395890abbc632fe58e188ba5120ef2d6ef070267809e878'


def verify(output, bundle, source_manifest):
    output.mkdir(parents=True, exist_ok=False)
    bundle.mkdir(parents=True, exist_ok=False)
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    routes = Routes.load(root)
    original_state = LocalState.snapshot(root)
    original_vault = (root / 'credentials.dpapi').read_bytes()
    identity = TLSIdentity.create(bundle / 'tls', original_state['deployment_id'], 'C:/Program Files/Git/usr/bin/openssl.exe')
    scope = {'tenant_id': 'internal', 'project_id': 'scientific-worker-proof-' + uuid.uuid4().hex}
    source = json.loads(source_manifest.read_bytes())
    owners = {name: dict(source['owners'][name]) for name in ('runtime', 'artifact')}

    def write(path, record):
        path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        return path

    for name, actions in (('runtime', ['claim', 'renew', 'complete']), ('artifact', ['read'])):
        settings = json.loads(Path(owners[name]['configuration']).read_bytes())
        reference = 'WORKER_' + name.upper() + '_TOKEN'
        settings['principals'].append({'token_env': 'AMPHORA_' + reference, 'actor_id': 'scientific-proof',
                                      'scope': scope, 'actions': actions})
        owners[name]['configuration'] = str(write(output / (name + '.json'), settings))
        owners[name]['secret_references'] = list(set(owners[name]['secret_references']) | {reference})
    manifest = write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    with ExitStack() as stack:
        ports = {}
        for name in ('runtime', 'artifact'):
            probe = stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            probe.bind(('127.0.0.1', 0))
            ports[name] = probe.getsockname()[1]
        assert not set(ports.values()).intersection(dict(routes.ports).values())
    access = write(output / 'access.json', {'profile': 'local-tool-access-v1',
        'identity_directory': str(identity.directory), 'ports': ports})
    tool_config = write(bundle / 'worker.json', {'actor_id': 'scientific-proof', 'scope': scope,
        'run_id': 'no-campaign-admitted', 'image_sha256': IMAGE[7:],
        'runtime': {'endpoint': 'https://host.docker.internal:' + str(ports['runtime']), 'token_env': 'AMPHORA_RUNTIME_TOKEN'},
        'artifacts': {'endpoint': 'https://host.docker.internal:' + str(ports['artifact']), 'token_env': 'AMPHORA_ARTIFACT_TOKEN'}})
    scientific = write(output / 'scientific.json', {'profile': 'local-scientific-workers-v1', 'workers': {
        'evolution-seed': {'image_id': IMAGE, 'configuration': str(tool_config), 'certificate': str(identity.certificate)}}})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    token = control_token(root)
    def request(endpoint, path, method='GET', credential=None):
        req = urllib.request.Request(endpoint + path, method=method,
            headers={} if credential is None else {'Authorization': 'Bearer ' + credential})
        try:
            response = opener.open(req, timeout=3)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read(65536))
    def control(path, method='GET', expected=200):
        status, record = request(routes.endpoint('supervisor'), path, method, token)
        assert status == expected, 'Unexpected local control status'
        return record
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    evidence = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'scope': scope,
                'controller_python': sys.executable, 'campaigns_admitted': 0, 'provider_calls': 0}
    with ProcessJob() as job:
        process = subprocess.Popen([sys.executable, '-I', '-m', 'amphora_deployment.lifecycle', 'serve',
            '--root', str(root), '--manifest', str(manifest), '--tool-access-manifest', str(access),
            '--scientific-manifest', str(scientific)], env=environment, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
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
                deadline = time.monotonic() + 60
                while True:
                    try:
                        assert request(routes.endpoint(owner), '/health' if owner == 'runtime' else '/ready')[0] == 200
                        break
                    except OSError:
                        assert control('/status')['owners'][owner]['state'] == 'running' and time.monotonic() < deadline
                        time.sleep(.2)
                control('/tool-access/' + owner + '/start', 'POST')
            control('/scientific-workers/evolution-seed/start', 'POST')
            started = time.monotonic()
            initial = control('/status')['scientific_workers']['evolution-seed']
            evidence['status_latency_seconds'] = round(time.monotonic() - started, 4)
            assert evidence['status_latency_seconds'] < .5
            assert initial['active_turn'], 'Required live accepted container turn was not observed'
            denied = control('/owners/runtime/drain', 'POST', 409)
            assert denied['error'] == 'container_requires_quiescence'
            control('/scientific-workers/evolution-seed/quiesce', 'POST')
            deadline = time.monotonic() + 60
            while True:
                worker = control('/status')['scientific_workers']['evolution-seed']
                if worker['completed_turns'] == 1:
                    break
                assert time.monotonic() < deadline, 'Scientific turn did not reconcile'
                time.sleep(.2)
            assert worker['exit_code'] == 3 and worker['faulted'] and not worker['active_turn']
            evidence['expected_owner_denial'] = worker
            control('/scientific-workers/evolution-seed/recover', 'POST')
            assert control('/status')['scientific_workers']['evolution-seed']['state'] == 'quiescent'
            for owner in owners:
                control('/tool-access/' + owner + '/drain', 'POST')
            deadline = time.monotonic() + 15
            while any(row['state'] != 'drained' for row in control('/status')['tool_access'].values()):
                assert time.monotonic() < deadline
                time.sleep(.1)
            for owner in owners:
                control('/owners/' + owner + '/drain', 'POST')
            deadline = time.monotonic() + 60
            while True:
                status = control('/status')
                if all(row['state'] == 'exited' for row in status['owners'].values()):
                    break
                assert time.monotonic() < deadline
                time.sleep(.2)
            assert all(row['exit_code'] == 0 for row in status['owners'].values())
            control('/shutdown', 'POST')
            assert process.wait(timeout=15) == 0
        finally:
            job.close()
            process.wait(timeout=15)
    require_released(root, original_state['deployment_id'])
    assert LocalState.snapshot(root) == original_state and (root / 'credentials.dpapi').read_bytes() == original_vault
    evidence.update(status='passed', early_api_drain_rejected=True, all_retained_turns_released=True,
        retained_bindings=len(retained_turns(root, original_state['deployment_id'])),
        limits=['Actual controller/Runtime/Data/TLS/Linux tool; nonexistent campaign intentionally rejects the claim',
                'No tool eligibility, successful scientific work, campaign admission or provider call',
                'Controller-death adoption and actual daemon-outage latency are separate probes'])
    write(output / 'evidence.json', evidence)
    print(json.dumps({'status': 'passed', 'expected_tool_exit': 3, 'provider_calls': 0}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bundle-directory', type=Path, required=True)
    parser.add_argument('--source-manifest', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output.absolute(), args.bundle_directory.absolute(), args.source_manifest.absolute())
