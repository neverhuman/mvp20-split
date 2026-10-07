"""Actual installed Registry/SQL heartbeat replay; zero capacity, no readiness claim."""

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.configuration import load_bindings
from amphora_deployment.lifecycle.events import LifecycleEvents
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.tool_catalog.credentials import provision_worker_credential, worker_credential
from amphora_deployment.tool_catalog.heartbeat import HeartbeatJournal, ReplicaBinding
from amphora_deployment.tool_catalog.transport import HeartbeatTransport

IMAGE = 'sha256:7538bece7dceb2f6c395890abbc632fe58e188ba5120ef2d6ef070267809e878'


def verify(output, source_manifest, registry_python):
    output.mkdir(parents=True, exist_ok=False)
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    original = LocalState.snapshot(root)
    original_vault = (root / 'credentials.dpapi').read_bytes()
    provision_worker_credential(root)
    scope = {'tenant_id': 'internal', 'project_id': 'catalog-delivery-' + uuid.uuid4().hex}
    routes = Routes.load(root)
    owner = dict(json.loads(source_manifest.read_bytes())['owners']['registry'])
    settings = json.loads(Path(owner['configuration']).read_bytes())
    settings['principals'] = [
        {'token_env': 'AMPHORA_REGISTRY_OPERATOR_TOKEN', 'actor_id': 'catalog-proof', 'scope': scope,
         'actions': ['register', 'activate', 'deploy', 'resolve', 'read']},
        {'token_env': 'AMPHORA_WORKER_REGISTRY_TOKEN', 'actor_id': 'science-slot', 'scope': scope,
         'actions': ['heartbeat']}]
    settings['resources'] = {'architecture': 'x86_64', 'operating_system': 'linux', 'cpu_millicores': 2000,
        'memory_mib': 1024, 'gpu_count': 0, 'timeout_seconds': 60, 'max_parallel_invocations': 1,
        'max_batch_size': 1}

    def write(path, value):
        path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        return path

    owner['configuration'] = str(write(output / 'registry.json', settings))
    owner['secret_references'] = ['REGISTRY_OPERATOR_TOKEN', 'WORKER_REGISTRY_TOKEN']
    manifest = write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': {'registry': owner}})
    command = ['docker', 'run', '--rm', '--network', 'none', '--read-only', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', IMAGE, 'describe', '--operation', 'seed', '--image-sha256', IMAGE[7:]]
    result = subprocess.run(command, capture_output=True, timeout=30)
    assert result.returncode == 0 and len(result.stdout) < 65536, 'Actual image descriptor probe failed'
    descriptor = json.loads(result.stdout)
    def wire(value):
        result = subprocess.run([str(registry_python), '-I', str(Path(__file__).with_name('catalog_contract_probe.py'))],
            input=json.dumps(value).encode(), capture_output=True, timeout=15,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert result.returncode == 0, 'Installed public contract validation failed'
        return json.loads(result.stdout)
    lock = wire({'operation': 'lock', 'descriptor': descriptor})
    write(output / 'release.json', {'descriptor': descriptor, 'lock': lock})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    admin = CredentialVault(root / 'credentials.dpapi', original['deployment_id']).load().environment(
        ['REGISTRY_OPERATOR_TOKEN'])['REGISTRY_OPERATOR_TOKEN']
    worker = worker_credential(root, original['deployment_id']).environment(['WORKER_REGISTRY_TOKEN'])['WORKER_REGISTRY_TOKEN']

    def request(path, payload=None):
        req = urllib.request.Request(routes.endpoint('registry') + path,
            data=None if payload is None else json.dumps(payload).encode(),
            headers={'Authorization': 'Bearer ' + admin, 'Content-Type': 'application/json'})
        with opener.open(req, timeout=3) as response:
            assert response.status == 200
            return json.loads(response.read(65536))

    def call(action, payload):
        body = {'identity': {'scope': scope, 'actor_id': 'catalog-proof', 'command_id': uuid.uuid4().hex,
                            'command_family': 'registry.' + action}, 'payload': payload}
        result = request('/v1/registry/' + action, body)
        assert result['status'] == ('rejected' if action == 'resolve' else 'accepted'), result['reason_code']
        return result

    observations = []
    with LocalState(root):
        binding = load_bindings(root, manifest, routes)['registry']
        with binding.launch(LifecycleEvents(output / 'events')) as process:
            deadline = time.monotonic() + 60
            while True:
                try:
                    request('/v1/releases')
                    break
                except urllib.error.HTTPError:
                    raise AssertionError('Registry authenticated catalog readiness failed') from None
                except OSError:
                    assert process.status()['state'] == 'running' and time.monotonic() < deadline
                    time.sleep(.2)
            call('register', {'scope': scope, 'descriptor': descriptor, 'expected_lock': lock})
            call('activate', {'release': lock, 'expected_revision': 1})
            call('deploy', {'deployment_id': 'seed', 'release': lock, 'architecture': 'x86_64',
                'operating_system': 'linux', 'workers': ['science-slot']})
            replica = ReplicaBinding(original['deployment_id'], scope['tenant_id'], scope['project_id'],
                                     'science-slot', 'seed', 'seed-slot')
            journal_path = root / 'tool-catalog' / (scope['project_id'] + '.json')
            journal = HeartbeatJournal(journal_path, replica)
            transport = HeartbeatTransport(routes.port('registry'), worker)
            first = journal.prepare(ready=False)
            lost = transport.send(first)  # Discard locally to model a lost response, not lost commit.
            assert wire({'operation': 'heartbeat', 'command': first, 'receipt': lost}) == {'status': 'valid'}
            journal = HeartbeatJournal(journal_path, replica)
            assert journal.prepare(ready=False) == first
            replay = transport.send(journal.prepare(ready=False))
            assert replay == lost
            observations.append(journal.accept(replay))
            second = journal.prepare(ready=False)
            assert second['identity']['command_id'] != first['identity']['command_id']
            observations.append(journal.accept(transport.send(second)))
            assert [row['revision'] for row in observations] == [1, 2]
            tool = descriptor['tool']
            decision = call('resolve', {'release': lock, 'context': 'synthetic-tests',
                                       'inputs': tool['inputs'], 'outputs': tool['outputs']})
            assert decision['decision']['status'] != 'candidate', 'Zero capacity cannot become eligible'
            process.drain()
            assert process.process.wait(timeout=60) == 0
    assert LocalState.snapshot(root) == original and (root / 'credentials.dpapi').read_bytes() == original_vault
    write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'scope': scope, 'release_lock': lock, 'observations': observations,
        'lost_response_exact_replay': True, 'zero_capacity_resolution': decision['decision'],
        'original_installation_unchanged': True, 'new_heartbeat_sidecar': True,
        'provider_calls': 0, 'limits': ['Actual installed Registry and SQL; caller records Deployment installation',
            'Linux image descriptor; no worker availability, successful execution or readiness claim',
            'Only zero-capacity observations; positive replay readiness policy has focused unit tests']})
    print('Actual Registry heartbeat replay and zero-capacity exclusion passed', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--source-manifest', required=True, type=Path)
    parser.add_argument('--registry-python', required=True, type=Path)
    args = parser.parse_args()
    verify(args.output.absolute(), args.source_manifest.absolute(), args.registry_python.absolute())
