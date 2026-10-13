"""Actual live proposal/successor browser recovery; no model call or new campaign."""
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from amphora_contracts_campaign_curation import parse_curation
from amphora_contracts_campaign_launch import parse_launch
from amphora_contracts_campaign_successor_launch import parse_successor_launch
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.persistence.state import LocalState
from campaign_curation_fixture.session import session
from campaign_curation_fixture.recovery import read, retained
from campaign_curation_fixture.verify import filtered_environment
from local_numeric_configuration import write
from .configuration import planning_python, worker_environment
from .run import owned_process


def verify(root, serving, qualification, previous, output):
    output.mkdir(parents=True, exist_ok=False)
    baseline = read(serving / 'integrated-evidence.json')
    folder = qualification / 'supported'
    current = read(folder / 'current-view.json')
    successor = read(folder / 'successor-evidence.json')
    assert read(folder / 'evidence.json')['status'] == 'passed'
    assert current['receipt']['phase'] == 'ready' and successor['run']['status'] == 'completed'
    scope = baseline['scope']; actor = [scope['tenant_id'], scope['project_id'], 'admin']
    curation = read(folder / 'original-receipt.json')
    curation_id = curation['reference']['curation_id']
    predecessor = baseline['predecessor']['run_id']
    seeds = []
    for prefix, key, command, receipt in (
        ('launch', actor, parse_launch((serving / 'original-launch-v3-command.json').read_bytes())[0], read(serving / 'original-launch-receipt.json')),
        ('curation', actor + [predecessor], parse_curation((folder / 'curation-command.json').read_bytes()), curation),
        ('successor', actor + [predecessor, curation_id], parse_successor_launch((folder / 'successor-launch-v3-command.json').read_bytes())[0], successor['launch'])):
        seeds.append({'key': 'amphora.' + prefix + '.v1:' + json.dumps(key, separators=(',', ':')),
            'value': json.dumps({'version': 1, 'body': command.canonical_bytes.decode(), 'receipt': receipt})})
    state = LocalState.snapshot(root)
    key = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(['GATEWAY_SESSION_KEY'])['GATEWAY_SESSION_KEY']
    histories = [(item / 'supported', read(item / 'supported/current-view.json')) for item in previous]
    def reconcile(api):
        retained(api, serving, baseline)
        for record_folder, view in [(folder, current), *histories]:
            assert api.call('planning', '/v1/campaign-curations/' + view['receipt']['reference']['curation_id']) == view
            assert api.call('planning', '/v1/campaign-curations', read(record_folder / 'curation-command.json'), allowed=(200, 202)) == read(record_folder / 'original-receipt.json')
        launch = successor['launch']
        assert api.call('deployment', '/v1/campaign-successor-launches/' + launch['identity']['command_id']) == launch
        assert api.call('deployment', '/v1/campaign-successor-launches', read(folder / 'successor-launch-v3-command.json'), allowed=(200, 202)) == launch
        assert api.call('runtime', '/v3/graph-runs/' + successor['run']['run_id']) == successor['run']
        assert api.call('runtime', '/v1/graph-runs/' + successor['run']['run_id'] + '/lineage') == successor['lineage']
    v2 = Path(__file__).absolute().parents[2]
    with session(root, serving) as api:
        reconcile(api)
        assert owned_process([planning_python(serving), '-I', Path(__file__).with_name('allowance.py'), qualification / 'curation-worker.json', output / 'final-allowance.json'], worker_environment(root, api), output / 'allowance.log', timeout=60) == 0
        allowance = read(output / 'final-allowance.json')
        assert allowance['reserved_slots'] == 16 and allowance['reserved_units'] == 4050000000
        assert allowance['remaining_slots'] == 37 and allowance['remaining_reservation_units'] == 9250000000
        browser_input = write(output / 'input.json', {'origin': api.controller.routes.endpoint('gateway'), 'seeds': seeds, 'predecessor': predecessor, 'successor': successor['run']['run_id'], 'curation_id': curation_id})
        with (output / 'browser.log').open('w', encoding='utf-8') as log:
            result = subprocess.run(['node', str(v2 / 'studio/tests/integration/curation_recovery.mjs'), str(browser_input), str(output)], cwd=v2 / 'studio', env=filtered_environment() | {'AMPHORA_BROWSER_LAUNCH_KEY': key}, stdout=log, stderr=log, timeout=180, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert result.returncode == 0, 'Actual live successor browser review failed; inspect browser.log'
        reconcile(api)
    write(output / 'owner-evidence.json', {'status': 'passed', 'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'provider_calls': 0, 'new_campaigns': 0, 'original_replay': 'unchanged', 'prior_failed_outcomes': len(histories), 'curation_id': curation_id, 'successor': successor['run']['run_id'], 'all_original_held_units': 4050000000, 'additional_allowance_remaining_units': 9250000000, 'scientific_validity': 'not_established'})
    print('Actual live supported proposal/successor recovery passed and drained', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'serving', 'qualification', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--previous', type=Path, nargs='+', required=True)
    args = parser.parse_args()
    verify(args.root.absolute(), args.serving.absolute(), args.qualification.absolute(), [p.absolute() for p in args.previous], args.output.absolute())
