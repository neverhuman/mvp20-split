"""Actual installed Runtime inspector through a server-side browser test gateway."""
import argparse
import json
import os
import secrets
import subprocess
from pathlib import Path

from sqlalchemy import URL

from postgres_fixture import owned_state
from supervision_owner_fixture.hosts import Owner
from verify_checkpoint_decision_read import retained_paths


def verify(output, python, retained):
    output.mkdir(parents=True, exist_ok=False)
    state = owned_state()
    host, port = state['endpoint'].split(':')
    sql = URL.create('postgresql+psycopg', username='runtime_service', password=state['password'],
                    host=host, port=int(port), database=state['database']).render_as_string(hide_password=False)
    original = json.loads((retained / 'evidence.json').read_text())
    ref = original['winner']['reference']
    config = retained_paths(json.loads((retained / 'runtime.json').read_text()), retained)
    token = secrets.token_hex(32)
    config['principals'] = [{'token_env': 'INSPECT_READ_TOKEN', 'actor_id': 'read-proof',
                            'scope': ref['scope'], 'actions': ['read']}]
    config['inspection'] = {'cursor_key_env': 'INSPECT_CURSOR_KEY'}
    env = dict(os.environ, CHECKPOINT_RUNTIME_SQL=sql, INSPECT_READ_TOKEN=token,
               INSPECT_CURSOR_KEY=secrets.token_hex(32), CHECKPOINT_DATA_TOKEN=secrets.token_hex(32))
    config_path = output / 'runtime.json'
    config_path.write_text(json.dumps(config), encoding='utf-8')
    owner = Owner(python, 'amphora_campaign_runtime', config_path, env, token, output)
    try:
        browser_env = dict(os.environ, SUPERVISION_BROWSER_ENDPOINT=owner.endpoint,
                           SUPERVISION_BROWSER_TOKEN=token,
                           SUPERVISION_BROWSER_BINDING=json.dumps({'run': ref['run_id'], 'scope': ref['scope']}))
        result = subprocess.run(['node', 'tests/browser/supervision.mjs'], cwd=Path(__file__).absolute().parents[1] / 'studio',
                                env=browser_env, capture_output=True, text=True, encoding='utf-8', timeout=90)
        (output / 'browser.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        assert result.returncode == 0, f'Browser failed; inspect {output / "browser.log"}'
        evidence_path = Path(result.stdout.strip().splitlines()[-1]) / 'evidence.json'
        evidence = json.loads(evidence_path.read_text())
        assert evidence['status'] == 'passed'
        evidence['runtime_package'] = '0.62.0'
        evidence['reference'] = ref
        evidence['source_evidence'] = str(evidence_path)
        (output / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
        print(f'Installed Runtime browser passed: {output / "evidence.json"}')
    finally:
        owner.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--runtime-python', required=True, type=Path)
    parser.add_argument('--retained', required=True, type=Path)
    args = parser.parse_args()
    verify(args.output.absolute(), args.runtime_python.absolute(), args.retained.absolute())
