"""Managed numeric campaign with owner context and one guarded live checkpoint."""

import argparse
import json
import os
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.scientific_workers.ownership import require_released
from amphora_deployment.tool_access import TLSIdentity
from check_boundaries import ROOT
from local_demo_controller import Controller
from local_numeric_campaign import Campaign
from local_numeric_configuration import bind_workers, write
from verify_local_live_checkpoint import key_from_authorized_file


def measure(configuration, output, routes, tokens, request):
    write(output / 'checkpoint-request.json', request)
    owners = json.loads((configuration / 'owners.json').read_bytes())['owners']
    python = Path(owners['planning']['installation']) / 'environment/Scripts/python.exe'
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment.update(PYTHONUTF8='1', PUBLIC_DATA_ENDPOINT=routes.endpoint('artifact'),
                       PUBLIC_DATA_TOKEN=tokens['PLANNING_DATA_TOKEN'])
    result = subprocess.run([str(python), '-I', str(ROOT / 'services/agent_planning/tests/checkpoint_openai/export_demo.py'),
        'measure', str(output)], env=environment, capture_output=True, timeout=45)
    (output / 'measurement.log').write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, 'Read-only owner packet measurement failed'
    return json.loads((output / 'measured.json').read_bytes())


def verify(configuration, output, *, key_file=None, science_only=False):
    assert not (science_only and key_file is not None), 'Scientific diagnostic must not load a provider credential'
    output.mkdir(parents=True, exist_ok=False)
    prepared = json.loads((configuration / 'prepared.json').read_bytes())
    material = prepared['material']
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    original, vault = LocalState.snapshot(root), (root / 'credentials.dpapi').read_bytes()
    routes = Routes.load(root)
    owners = json.loads((configuration / 'owners.json').read_bytes())['owners']
    runtime_python = Path(owners['runtime']['installation']) / 'environment/Scripts/python.exe'
    tokens = CredentialVault(root / 'credentials.dpapi', original['deployment_id']).load().environment([
        'REGISTRY_OPERATOR_TOKEN', 'RUNTIME_OPERATOR_TOKEN', 'ARTIFACT_OPERATOR_TOKEN', 'RUNTIME_ARTIFACT_TOKEN',
        'RUNTIME_PLANNING_TOKEN', 'PLANNING_DATA_TOKEN', 'RESEARCH_OPERATOR_TOKEN', 'KNOWLEDGE_OPERATOR_TOKEN'])
    # The supervisor validates configured key presence even while the worker is stopped.
    # Dry mode never starts Planning; this marker is not a provider credential.
    key = 'dry-preflight-no-provider-credential' if key_file is None else key_from_authorized_file(key_file)
    controller, campaign, final = None, None, None
    try:
        controller = Controller(root, configuration, routes, 'standby', model_key=key)
        campaign = Campaign(controller, configuration, material, tokens, runtime_python)
        controller.start_owners(tokens['REGISTRY_OPERATOR_TOKEN'])
        def registry(action, payload):
            receipt = campaign.call('registry', '/v1/registry/' + action, campaign.identity('registry.' + action, payload))
            assert receipt['status'] == 'accepted', receipt['reason_code']
            return receipt
        for stage, lock in material['locks'].items():
            registry('register', {'scope': material['scope'], 'descriptor': campaign.releases[stage], 'expected_lock': lock})
            release = campaign.call('registry', '/v1/releases/' + lock['descriptor_sha256'])
            assert release['status'] in ('registered', 'active'), 'Existing release cannot be silently reactivated'
            if release['status'] == 'registered':
                registry('activate', {'release': lock, 'expected_revision': release['revision']})
            registry('deploy', {'deployment_id': stage, 'release': lock, 'architecture': 'x86_64',
                               'operating_system': 'linux', 'workers': ['science-slot']})
        run_id = campaign.admit(supervision_policy=None if science_only else prepared['compiled']['policy_sha256'])
        write(output / 'admission.json', {'scope': material['scope'], 'run_id': run_id,
            'command': campaign.admission_command, 'receipt': campaign.admission})
        before = campaign.graph()
        first_drain = controller.drain()
        controller.close()
        controller = None
        identity = TLSIdentity.load(Path(prepared['identity_directory']))
        label = 'admitted-' + uuid.uuid4().hex
        bind_workers(configuration, Path(prepared['identity_directory']).parent, material, identity,
                     prepared['ports'], run_id, label)
        controller = Controller(root, configuration, routes, label, model_key=key)
        key = None
        campaign.controller = controller
        controller.start_owners(tokens['REGISTRY_OPERATOR_TOKEN'])
        assert campaign.graph() == before
        assert campaign.call('runtime', campaign.admission_path, campaign.admission_command) == campaign.admission
        for name in controller.control('/status')['scientific_workers']:
            controller.control('/scientific-workers/' + name + '/standby', 'POST')
        controller.wait(lambda: all(row['state'] == 'observed' and row['observation']['free_slots'] == 1
                        for row in controller.control('/status')['tool_catalog'].values()))
        for stage, descriptor in campaign.releases.items():
            resolved = registry('resolve', {'release': material['locks'][stage], 'context': 'synthetic-tests',
                'inputs': descriptor['tool']['inputs'], 'outputs': descriptor['tool']['outputs']})
            assert resolved['decision']['status'] == 'candidate'
        for name in ('runtime-deliver', 'runtime-checkpoint', 'runtime-coordinate'):
            controller.control('/workers/' + name + '/start', 'POST')
        started = time.monotonic()
        def original_request():
            page = campaign.call('runtime', '/v1/supervision/runs/' + run_id + '/checkpoints')
            if not page['items'] or page['items'][0]['requests'] != 1:
                return None
            item = page['items'][0]
            requests = campaign.call('runtime', '/v1/supervision/runs/' + run_id + '/checkpoints/' +
                item['reference']['decision_id'] + '/requests?snapshot_token=' + quote(page['snapshot']['snapshot_token'], safe=''))
            if len(requests['items']) != 1:
                return None
            engagement = requests['items'][0]['engagement']['engagement_id']
            code, request = controller.request(routes.endpoint('planning'), '/v2/supervision/requests/' + engagement,
                                               token=tokens['RUNTIME_PLANNING_TOKEN'])
            return request if code == 200 else None
        measured = None
        if not science_only:
            request = controller.wait(original_request, timeout=90)
            measured = measure(configuration, output, routes, tokens, request)
            entries = request['planning_request']['context']['entries']
            assert any(row['artifact'] == prepared['context'] and row['required'] for row in entries)
            write(output / 'preflight.json', {'run_id': run_id, 'measurement': measured,
                'context': prepared['context'], 'provider_started': False})
            assert measured['fit']['fits'], 'Required integrated context exceeds unchanged input allowance; no paid call made'
        if key_file is None and not science_only:
            cancellation = campaign.cancel_after_failure()
            final = controller.drain()
            write(output / 'evidence.json', {'status': 'preflight_passed', 'run_id': run_id, 'measured': measured,
                'provider_calls': 0, 'cancellation': cancellation, 'final': final})
            print('Required owner context fits; dry preflight cancelled before model/scientific execution', flush=True)
            return
        if not science_only:
            controller.control('/workers/planning-checkpoint/start', 'POST')
        for name in controller.control('/status')['scientific_workers']:
            controller.control('/scientific-workers/' + name + '/start', 'POST')
        previous, latencies = None, []
        while True:
            graph = campaign.graph()
            tick = time.monotonic()
            status = controller.control('/status')
            latencies.append(time.monotonic() - tick)
            page = campaign.call('runtime', '/v1/supervision/runs/' + run_id + '/checkpoints')
            write(output / 'latest.json', {'graph': graph, 'controller': status, 'checkpoints': page})
            observed = (graph['status'], graph['spent'], tuple(row['winner_kind'] for row in page['items']))
            if observed != previous:
                print(json.dumps({'state': observed}), flush=True)
                previous = observed
            if graph['status'] != 'running':
                break
            assert not any(row['faulted'] for row in status['workers'].values()), 'Native worker faulted'
            assert time.monotonic() - started < 600, 'Integrated campaign exceeded600second bound'
            assert latencies[-1] < .5, 'Controller response exceeded0.5second bound'
            time.sleep(1)
        for name in status['scientific_workers']:
            controller.control('/scientific-workers/' + name + '/quiesce', 'POST')
        controller.wait(lambda: all(not row['active_turn'] for row in controller.control('/status')['scientific_workers'].values()))
        campaign.output = output
        result = campaign.evidence()
        decision = None
        if not science_only:
            item, = page['items']
            decision = campaign.call('runtime', '/v1/supervision/decisions/' + run_id + '/' + item['reference']['decision_id'])
        final = controller.drain()
        require_released(root, original['deployment_id'])
        assert LocalState.snapshot(root) == original and (root / 'credentials.dpapi').read_bytes() == vault
        record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'science_only_passed' if science_only else 'passed' if item['winner_kind'] == 'model_accepted' else 'model_gate_not_passed',
            'run_id': run_id, 'scope': material['scope'], 'result': result, 'decision': decision,
            'checkpoints': page, 'measured': measured, 'context': prepared['context'],
            'elapsed_seconds': time.monotonic() - started, 'maximum_control_latency_seconds': max(latencies),
            'prebinding_drain': first_drain, 'final': final,
            'limits': ['Synthetic deterministic numeric graph, not scientific efficacy or LLM-authored topology',
                'Context is an explicit projection of exact public Research/Knowledge readback',
                'Model consumption/cost and immutable restart require separate readback; browser trace unverified']}
        write(output / 'evidence.json', record)
        assert record['status'] in ('passed', 'science_only_passed'), 'Scientific result retained but model gate did not pass'
        print('Managed scientific campaign and model checkpoint completed; retained usage/context readback next', flush=True)
    except BaseException as error:
        failure = {'error_type': type(error).__name__, 'run_id': None if campaign is None else campaign.run_id}
        if controller is not None and controller.process.poll() is None and final is None:
            try:
                if campaign is not None:
                    failure['cancel'] = campaign.cancel_after_failure()
                failure['drain'] = controller.drain()
            except Exception as cleanup:
                failure['cleanup_error_type'] = type(cleanup).__name__
        write(output / 'failure.json', failure)
        raise
    finally:
        if controller is not None:
            controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configuration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--key-file', type=Path, help='Explicit live execution; omitted means zero-call preflight')
    parser.add_argument('--science-only', action='store_true', help='Separate unsupervised graph diagnostic; zero model calls')
    args = parser.parse_args()
    verify(args.configuration.absolute(), args.output.absolute(), key_file=args.key_file, science_only=args.science_only)
