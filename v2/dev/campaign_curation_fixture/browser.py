"""Production browser recovery of actual retained curation and successor records."""
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
from local_numeric_configuration import write
from .session import session
from .recovery import read, retained
from .verify import filtered_environment


def verify(root, serving, output):
    output.mkdir(parents=True, exist_ok=False)
    evidence = read(serving / 'integrated-evidence.json')
    assert read(serving / 'recovery-evidence.json')['status'] == 'passed'
    scope = evidence['scope']
    actor = [scope['tenant_id'], scope['project_id'], 'admin']
    curation = read(serving / 'curation-02/curation-original-receipt.json')
    curation_id = curation['reference']['curation_id']
    predecessor = evidence['predecessor']['run_id']
    seeds = []
    for prefix, key, command, receipt in (
        ('launch', actor, parse_launch((serving / 'original-launch-v3-command.json').read_bytes())[0],
         read(serving / 'original-launch-receipt.json')),
        ('curation', actor + [predecessor], parse_curation((serving / 'curation-02/curation-command.json').read_bytes()), curation),
        ('successor', actor + [predecessor, curation_id], parse_successor_launch((serving / 'successor-launch-v3-command.json').read_bytes())[0],
         evidence['successor_launch'])):
        seeds.append({'key': 'amphora.' + prefix + '.v1:' + json.dumps(key, separators=(',', ':')),
            'value': json.dumps({'version': 1, 'body': command.canonical_bytes.decode(), 'receipt': receipt})})
    gateway = read(serving / 'gateway.json')
    gateway['context']['run_id'] = predecessor
    write(serving / 'gateway.json', gateway)
    state = LocalState.snapshot(root)
    key = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(['GATEWAY_SESSION_KEY'])['GATEWAY_SESSION_KEY']
    environment = filtered_environment() | {'AMPHORA_BROWSER_LAUNCH_KEY': key}
    v2 = Path(__file__).absolute().parents[2]
    with session(root, serving) as api:
        retained(api, serving, evidence)
        browser_input = write(output / 'input.json', {'origin': api.controller.routes.endpoint('gateway'),
            'seeds': seeds, 'predecessor': predecessor, 'successor': evidence['successor']['run_id'],
            'curation_id': curation_id})
        with (output / 'browser.log').open('w', encoding='utf-8') as log:
            result = subprocess.run(['node', str(v2 / 'studio/tests/integration/curation_recovery.mjs'),
                str(browser_input), str(output)], cwd=v2 / 'studio', env=environment,
                stdout=log, stderr=log, timeout=180, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        assert result.returncode == 0, 'Actual browser recovery failed; inspect browser.log'
        retained(api, serving, evidence)
    write(output / 'owner-evidence.json', {'status': 'passed',
        'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'browser': read(output / 'browser-evidence.json'),
        'provider_calls': 0, 'new_campaigns': 0,
        'scope': 'Recovery of exact existing commands through production entry and actual owner APIs'})
    print('Actual curation/successor browser recovery passed and drained', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--serving', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify(args.root.absolute(), args.serving.absolute(), args.output.absolute())
