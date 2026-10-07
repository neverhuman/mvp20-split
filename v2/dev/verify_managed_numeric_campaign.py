"""Actual local managed two-generation numeric campaign; synthetic, no model calls."""

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
from amphora_deployment.scientific_workers.ownership import require_released

from local_demo_controller import Controller
from local_numeric_campaign import Campaign
from local_numeric_configuration import bind_workers, prepare, write


def verify(output, bundle, materials, source_manifest, *, fixture_root=None, root=None):
    root = root or Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    original = LocalState.snapshot(root)
    vault = (root / 'credentials.dpapi').read_bytes()
    routes = Routes.load(root)
    material, identity, ports = prepare(output, bundle, materials, source_manifest, original['deployment_id'], routes,
        project='managed-campaign-' + uuid.uuid4().hex, delivery=True)
    bind_workers(output, bundle, material, identity, ports, 'awaiting-admission', 'standby')
    owners = json.loads((output / 'owners.json').read_bytes())['owners']
    runtime_python = Path(owners['runtime']['installation']) / 'environment/Scripts/python.exe'
    tokens = CredentialVault(root / 'credentials.dpapi', original['deployment_id']).load().environment([
        'REGISTRY_OPERATOR_TOKEN', 'RUNTIME_OPERATOR_TOKEN', 'ARTIFACT_OPERATOR_TOKEN', 'RUNTIME_ARTIFACT_TOKEN'])
    controller = Controller(root, output, routes, 'standby')
    campaign = None
    try:
        campaign = Campaign(controller, output, material, tokens, runtime_python, fixture_root=fixture_root)
        controller.start_owners(tokens['REGISTRY_OPERATOR_TOKEN'])
        def registry(action, payload):
            receipt = campaign.call('registry', '/v1/registry/' + action, campaign.identity('registry.' + action, payload))
            assert receipt['status'] == 'accepted', receipt['reason_code']
            return receipt
        for stage, lock in material['locks'].items():
            descriptor = campaign.releases[stage]
            registry('register', {'scope': material['scope'], 'descriptor': descriptor, 'expected_lock': lock})
            registry('activate', {'release': lock, 'expected_revision': 1})
            registry('deploy', {'deployment_id': stage, 'release': lock, 'architecture': 'x86_64',
                               'operating_system': 'linux', 'workers': ['science-slot']})
        def standby():
            for name in controller.control('/status')['scientific_workers']:
                controller.control('/scientific-workers/' + name + '/standby', 'POST')
            controller.wait(lambda: all(row['state'] == 'observed' and row['observation']['free_slots'] == 1
                            for row in controller.control('/status')['tool_catalog'].values()))
        standby()
        candidates = {stage: registry('resolve', {'release': material['locks'][stage], 'context': 'synthetic-tests',
            'inputs': descriptor['tool']['inputs'], 'outputs': descriptor['tool']['outputs']})
            for stage, descriptor in campaign.releases.items()}
        assert all(value['decision']['status'] == 'candidate' for value in candidates.values())
        run_id = campaign.admit()
        write(output / 'admission.json', {'scope': material['scope'], 'run_id': run_id, 'receipt': campaign.admission,
                                        'command': campaign.admission_command})
        before = campaign.graph()
        assert before['status'] == 'running' and before['spent'] == 0
        first_drain = controller.drain()
        controller.close()
        controller = None
        bind_workers(output, bundle, material, identity, ports, run_id, 'admitted')
        controller = Controller(root, output, routes, 'admitted')
        campaign.controller = controller
        controller.start_owners(tokens['REGISTRY_OPERATOR_TOKEN'])
        assert campaign.graph() == before
        assert campaign.call('runtime', '/v1/graph-runs', campaign.admission_command) == campaign.admission
        standby()
        for name in ('runtime-deliver', 'runtime-coordinate'):
            controller.control('/workers/' + name + '/start', 'POST')
        for name in controller.control('/status')['scientific_workers']:
            controller.control('/scientific-workers/' + name + '/start', 'POST')
        started = time.monotonic()
        deadline = started + 600
        previous = None
        latencies = []
        while True:
            graph = campaign.graph()
            # Public timing metadata makes a later process fault diagnosable without
            # enabling raw container logs, exposing credentials or reading owner SQL.
            active = campaign.call('runtime', '/v1/runs/' + run_id)
            with (output / 'active-attempts.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps({'observed_at': datetime.now().astimezone().isoformat(),
                                         'run': active}, separators=(',', ':')) + '\n')
            state = (graph['status'], graph['spent'])
            if state != previous:
                print(json.dumps({'campaign': graph['status'], 'accepted_budget_spend': graph['spent']}), flush=True)
                previous = state
            tick = time.monotonic()
            status = controller.control('/status')
            latencies.append(time.monotonic() - tick)
            assert latencies[-1] < .5, 'Managed control latency bound exceeded'
            write(output / 'latest-observation.json', {'graph': graph, 'controller': status})
            if graph['status'] != 'running':
                assert graph['status'] == 'completed', 'Graph ended without successful completion'
                break
            assert not any(row['faulted'] for row in status['workers'].values()), 'Native worker faulted'
            assert not any(row['faulted'] for row in status['scientific_workers'].values()), 'Scientific worker faulted'
            assert time.monotonic() < deadline, 'Managed campaign exceeded predeclared600second bound'
            time.sleep(1)
        elapsed = time.monotonic() - started
        for name in status['scientific_workers']:
            controller.control('/scientific-workers/' + name + '/quiesce', 'POST')
        controller.wait(lambda: all(not row['active_turn'] for row in controller.control('/status')['scientific_workers'].values()))
        result = campaign.evidence()
        final = controller.drain()
        require_released(root, original['deployment_id'])
        assert LocalState.snapshot(root) == original and (root / 'credentials.dpapi').read_bytes() == vault
        write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed', 'scope': material['scope'], 'run_id': run_id, 'result': result,
            'candidates': {stage: value['decision'] for stage, value in candidates.items()},
            'prebinding_drain': first_drain, 'completed_controller': status, 'final_controller': final,
            'execution_seconds': elapsed, 'execution_limit_seconds': 600,
            'maximum_control_latency_seconds': max(latencies), 'control_latency_limit_seconds': .5,
            'original_installation_unchanged': True, 'provider_calls': 0,
            'limits': ['Actual installed owners and Linux scientific images; source Deployment controller',
                'Synthetic deterministic numeric graph, not scientific efficacy or LLM-generated topology',
                'Owner-local test compiler computes reviewed fixture plan identity without SQL credentials',
                'Explicit graceful admission-to-worker-binding restart, not crash recovery or in-campaign human editing',
                'Original scope/receipts/state preserved; no migrations, resets or paid provider calls']})
        print('Managed campaign completed15 scientific invocations,6 evaluations and3 selection checkpoints', flush=True)
    except BaseException as error:
        failure = {'status': 'failed', 'error_type': type(error).__name__,
                   'run_id': None if campaign is None else campaign.run_id}
        if controller is not None and controller.process.poll() is None:
            try:
                if campaign is not None:
                    failure['cancellation'] = campaign.cancel_after_failure()
                failure['cleanup'] = controller.drain()
            except Exception as cleanup_error:
                failure['cleanup_error_type'] = type(cleanup_error).__name__
        write(output / 'failure.json', failure)
        raise
    finally:
        if controller is not None:
            controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'bundle-directory', 'materials', 'source-manifest'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--fixture-root', type=Path)
    parser.add_argument('--root', type=Path)
    args = parser.parse_args()
    verify(args.output.absolute(), args.bundle_directory.absolute(), args.materials.absolute(), args.source_manifest.absolute(),
           fixture_root=None if args.fixture_root is None else args.fixture_root.absolute(),
           root=None if args.root is None else args.root.absolute())
