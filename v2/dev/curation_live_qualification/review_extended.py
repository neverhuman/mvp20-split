"""Actual failed-graph and valid capability-request review; no provider enabled."""
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

from amphora_contracts_campaign_launch import parse_launch
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.persistence.state import LocalState
from campaign_curation_fixture.recovery import read, retained
from campaign_curation_fixture.session import session
from campaign_curation_fixture.verify import filtered_environment
from local_numeric_configuration import write
from .configuration import planning_python, worker_environment
from .run import owned_process


def verify(root, serving, qualification, prior, output):
    output.mkdir(parents=True, exist_ok=False)
    original = read(serving / 'integrated-evidence.json')
    scope = original['scope']; actor = [scope['tenant_id'], scope['project_id'], 'admin']
    launch = parse_launch((serving / 'original-launch-v3-command.json').read_bytes())[0]
    seeds = [{'key': 'amphora.launch.v1:' + json.dumps(actor, separators=(',', ':')),
              'value': json.dumps({'version': 1, 'body': launch.canonical_bytes.decode(),
                                  'receipt': read(serving / 'original-launch-receipt.json')})}]
    state = LocalState.snapshot(root)
    key = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(
        ['GATEWAY_SESSION_KEY'])['GATEWAY_SESSION_KEY']
    v2 = Path(__file__).absolute().parents[2]
    folders = {'supported': qualification / 'supported', 'missing': prior / 'missing'}
    saved = {name: read(folder / 'current-view.json') for name, folder in folders.items()}
    capabilities = read(prior / 'missing/capability-requests.json')
    assert saved['supported']['receipt']['phase'] == 'indeterminate'
    assert saved['missing']['proposal']['outcome']['kind'] == 'request_capabilities'
    assert all(row['fulfillment'] is None for row in capabilities)
    def reconcile(api):
        retained(api, serving, original)
        for name, view in saved.items():
            assert api.call('planning', '/v1/campaign-curations/' + view['receipt']['reference']['curation_id']) == view
            assert api.call('planning', '/v1/campaign-curations', read(folders[name] / 'curation-command.json'),
                allowed=(200, 202)) == read(folders[name] / 'original-receipt.json')
        for row in capabilities:
            assert api.call('planning', '/v1/capability-requests/' + row['reference']['request_id']) == row
    with session(root, serving) as api:
        reconcile(api)
        assert owned_process([planning_python(serving), '-I', Path(__file__).with_name('allowance.py'),
            qualification / 'curation-worker.json', output / 'final-allowance.json'],
            worker_environment(root, api), output / 'allowance.log', timeout=60) == 0
        allowance = read(output / 'final-allowance.json')
        assert allowance['reserved_slots'] == 10 and allowance['reserved_units'] == 2550000000
        assert allowance['remaining_slots'] == allowance['remaining_reservation_units'] == 0
        browser_input = write(output / 'input.json', {'origin': api.controller.routes.endpoint('gateway'),
            'seeds': seeds, 'failure_label': 'Outcome unknown', 'failed': saved['supported']['receipt']['reference']['curation_id'],
            'missing': saved['missing']['receipt']['reference']['curation_id'],
            'capabilities': [{'purpose': row['gap']['purpose'], 'request_id': row['reference']['request_id']} for row in capabilities]})
        with (output / 'browser.log').open('w', encoding='utf-8') as log:
            result = subprocess.run(['node', str(v2 / 'studio/tests/integration/curation_live_review.mjs'),
                str(browser_input), str(output)], cwd=v2 / 'studio',
                env=filtered_environment() | {'AMPHORA_BROWSER_LAUNCH_KEY': key}, stdout=log, stderr=log,
                timeout=180, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert result.returncode == 0, 'Actual live outcome browser review failed; inspect browser.log'
        reconcile(api)
    write(output / 'owner-evidence.json', {'status': 'passed', 'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'scope': scope, 'original_receipt_replay': 'unchanged', 'provider_calls_this_probe': 0,
        'supported_live_gate': 'indeterminate', 'missing_capability_gate': 'passed',
        'capabilities': [row['reference'] for row in capabilities], 'all_original_held_units': 2550000000,
        'scientific_validity': 'not_established'})
    print('Actual08d extended-output indeterminate outcome browser review passed and drained', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'serving', 'qualification', 'prior', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    verify(*(getattr(args, name).absolute() for name in ('root', 'serving', 'qualification', 'prior', 'output')))
