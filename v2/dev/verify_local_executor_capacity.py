"""Actual managed standby/Registry eligibility/withdrawal; no campaign admission."""

import argparse
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.tool_catalog.credentials import provision_worker_credential

from local_demo_controller import Controller
from local_numeric_configuration import bind_workers, prepare, write


def verify(output, bundle, materials, source_manifest):
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    original = LocalState.snapshot(root)
    vault_bytes = (root / 'credentials.dpapi').read_bytes()
    provision_worker_credential(root)
    routes = Routes.load(root)
    material, identity, ports = prepare(output, bundle, materials, source_manifest, original['deployment_id'], routes,
                                       project='managed-capacity-' + uuid.uuid4().hex)
    bind_workers(output, bundle, material, identity, ports, 'awaiting-admission', 'standby')
    tokens = CredentialVault(root / 'credentials.dpapi', original['deployment_id']).load().environment(['REGISTRY_OPERATOR_TOKEN'])
    controller = Controller(root, output, routes, 'standby')
    scope, candidates = material['scope'], {}
    def call(action, payload):
        command = {'identity': {'scope': scope, 'actor_id': 'admin', 'command_id': uuid.uuid4().hex,
                               'command_family': 'registry.' + action}, 'payload': payload}
        code, receipt = controller.request(routes.endpoint('registry'), '/v1/registry/' + action,
                                           token=tokens['REGISTRY_OPERATOR_TOKEN'], body=command)
        assert code == 200, 'Registry public command failed'
        return receipt
    try:
        controller.start_owners(tokens['REGISTRY_OPERATOR_TOKEN'])
        assert all(row['state'] == 'quiescent' for row in controller.control('/status')['scientific_workers'].values())
        for stage, lock in material['locks'].items():
            descriptor = json.loads((output / (stage + '-descriptor.json')).read_bytes())
            assert call('register', {'scope': scope, 'descriptor': descriptor, 'expected_lock': lock})['status'] == 'accepted'
            assert call('activate', {'release': lock, 'expected_revision': 1})['status'] == 'accepted'
            assert call('deploy', {'deployment_id': stage, 'release': lock, 'architecture': 'x86_64',
                'operating_system': 'linux', 'workers': ['science-slot']})['status'] == 'accepted'
            request = {'release': lock, 'context': 'synthetic-tests', 'inputs': descriptor['tool']['inputs'],
                       'outputs': descriptor['tool']['outputs']}
            assert call('resolve', request)['decision']['status'] != 'candidate'
            candidates[stage] = request
        for name in controller.control('/status')['scientific_workers']:
            controller.control('/scientific-workers/' + name + '/standby', 'POST')
        def observed():
            status = controller.control('/status')
            return all(row['state'] == 'observed' and row['observation']['free_slots'] == 1
                       for row in status['tool_catalog'].values()) and status
        ready = controller.wait(observed)
        started = time.monotonic()
        controller.control('/status')
        latency = time.monotonic() - started
        assert latency < .5
        selected = {stage: call('resolve', request) for stage, request in candidates.items()}
        assert all(row['decision']['status'] == 'candidate' for row in selected.values())
        assert all(row['completed_turns'] == 0 and not row['active_turn'] for row in ready['scientific_workers'].values())
        for name in ready['scientific_workers']:
            controller.control('/scientific-workers/' + name + '/quiesce', 'POST')
        controller.wait(lambda: all(row['state'] == 'observed' and row['observation']['free_slots'] == 0
                        for row in controller.control('/status')['tool_catalog'].values()))
        withdrawn = {stage: call('resolve', request) for stage, request in candidates.items()}
        assert all(row['decision']['status'] != 'candidate' for row in withdrawn.values())
        final = controller.drain()
    finally:
        controller.close()
    assert LocalState.snapshot(root) == original and (root / 'credentials.dpapi').read_bytes() == vault_bytes
    write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'scope': scope, 'ready': ready, 'selected': selected, 'withdrawn': withdrawn,
        'final': final, 'status_latency_seconds': latency, 'predeclared_status_limit_seconds': .5,
        'campaigns_admitted': 0, 'provider_calls': 0, 'original_installation_unchanged': True,
        'limits': ['Actual installed Runtime/Data/Registry and TLS, Docker image/resource checks, source Deployment controller',
            'Standby capacity and withdrawal only; no successful scientific invocation or campaign admission',
            'Runtime health is configured-execution liveness, not continuous SQL readiness',
            'Capacity is expiring observation, not exclusive physical reservation or dispatch authority']})
    print('All five managed executors became candidates only in standby and withdrew on quiesce', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'bundle-directory', 'materials', 'source-manifest'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    verify(args.output.absolute(), args.bundle_directory.absolute(), args.materials.absolute(), args.source_manifest.absolute())
