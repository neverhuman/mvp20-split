"""Actual-owner failure review and original accounting; no provider configuration enabled."""
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


def verify(root, serving, qualification, output):
    output.mkdir(parents=True, exist_ok=False)
    original = read(serving / 'integrated-evidence.json')
    scope = original['scope']
    actor = [scope['tenant_id'], scope['project_id'], 'admin']
    launch = parse_launch((serving / 'original-launch-v3-command.json').read_bytes())[0]
    seeds = [{'key': 'amphora.launch.v1:' + json.dumps(actor, separators=(',', ':')),
              'value': json.dumps({'version': 1, 'body': launch.canonical_bytes.decode(),
                                  'receipt': read(serving / 'original-launch-receipt.json')})}]
    state = LocalState.snapshot(root)
    key = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(
        ['GATEWAY_SESSION_KEY'])['GATEWAY_SESSION_KEY']
    v2 = Path(__file__).absolute().parents[2]
    records = []
    with session(root, serving) as api:
        retained(api, serving, original)
        for name in ('supported', 'missing'):
            saved = read(qualification / name / 'current-view.json')
            reference = saved['receipt']['reference']['curation_id']
            assert api.call('planning', '/v1/campaign-curations/' + reference) == saved
            assert saved['receipt']['phase'] == 'failed' and saved['receipt']['reason_code'] == 'model_output_invalid'
            assert saved['proposal'] is None and saved['validated_draft'] is None and not saved['capability_requests']
            assert api.call('planning', '/v1/campaign-curations', read(qualification / name / 'curation-command.json'),
                            allowed=(200, 202)) == read(qualification / name / 'original-receipt.json')
            records.append({'scenario': name, 'curation_id': reference,
                            'output_sha256': saved['provider']['output_sha256']})
        environment = worker_environment(root, api)
        assert owned_process([planning_python(serving), '-I', Path(__file__).with_name('allowance.py'),
            qualification / 'curation-worker.json', output / 'final-allowance.json'],
            environment, output / 'allowance.log', timeout=60) == 0
        allowance = read(output / 'final-allowance.json')
        assert allowance['reserved_slots'] == 4 and allowance['reserved_units'] == 1000000000
        assert allowance['remaining_slots'] == allowance['remaining_reservation_units'] == 0
        browser_input = write(output / 'input.json', {'origin': api.controller.routes.endpoint('gateway'),
            'seeds': seeds, 'records': records})
        with (output / 'browser.log').open('w', encoding='utf-8') as log:
            result = subprocess.run(['node', str(v2 / 'studio/tests/integration/curation_live_failure.mjs'),
                str(browser_input), str(output)], cwd=v2 / 'studio',
                env=filtered_environment() | {'AMPHORA_BROWSER_LAUNCH_KEY': key},
                stdout=log, stderr=log, timeout=180, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert result.returncode == 0, 'Actual failure browser probe failed; inspect browser.log'
        for record in records:
            assert api.call('planning', '/v1/campaign-curations/' + record['curation_id']) == read(
                qualification / record['scenario'] / 'current-view.json')
        retained(api, serving, original)
    costs = [read(qualification / name / 'provider-accounting.json')['usage']['accounting_units']
             for name in ('supported', 'missing')]
    write(output / 'owner-evidence.json', {'status': 'passed', 'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'scope': scope, 'failure_records': records, 'original_receipt_replay': 'unchanged',
        'provider_calls_this_probe': 0, 'qualification_live_calls': 2, 'reported_live_cost_units': sum(costs),
        'original_held_units_including_P4': allowance['reserved_units'], 'scientific_validity': 'not_established'})
    print('Actual live-failure browser/accounting recovery passed and drained', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'serving', 'qualification', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    verify(*(getattr(args, name).absolute() for name in ('root', 'serving', 'qualification', 'output')))
