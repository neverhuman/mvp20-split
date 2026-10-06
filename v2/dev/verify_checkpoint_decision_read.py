"""Read retained owner-proof winners through a fresh isolated Runtime HTTP process."""

import argparse
import hashlib
import json
import os
import secrets
from datetime import datetime
from pathlib import Path

from sqlalchemy import URL

from install_owner_peer import install
from postgres_fixture import owned_state
from supervision_owner_fixture.hosts import Owner


def retained_paths(value, root):
    if isinstance(value, dict):
        return {key: retained_paths(item, root) for key, item in value.items()}
    if isinstance(value, list):
        return [retained_paths(item, root) for item in value]
    if isinstance(value, str) and value.endswith('.json') and '://' not in value and (root / value).is_file():
        return str((root / value).absolute())
    return value


def verify(output, retained):
    python = install(output / 'installation', 'amphora-campaign-runtime',
                     ['amphora_agent_planning', 'amphora_data_artifacts'])
    state = owned_state()
    host, port = state['endpoint'].split(':')
    sql = URL.create('postgresql+psycopg', username='runtime_service', password=state['password'],
        host=host, port=int(port), database=state['database']).render_as_string(hide_password=False)
    records = []
    for index, root in enumerate(retained):
        original = json.loads((root / 'evidence.json').read_text())
        winner = original['winner']
        reference = winner['reference']
        config = json.loads((root / 'runtime.json').read_text())
        # Preserve reviewed graph/schema/recipe paths without moving retained artifacts.
        config = retained_paths(config, root)
        token = secrets.token_hex(32)
        config['principals'] = [{'token_env': 'DECISION_READ_TOKEN', 'actor_id': 'read-proof',
            'scope': reference['scope'], 'actions': ['read']}]
        env = dict(os.environ, CHECKPOINT_RUNTIME_SQL=sql, DECISION_READ_TOKEN=token,
                   CHECKPOINT_DATA_TOKEN=secrets.token_hex(32))
        config_path = output / f'configuration-{index}.json'
        config_path.write_text(json.dumps(config), encoding='utf-8')
        path = f"/v1/supervision/decisions/{reference['run_id']}/{reference['decision_id']}"
        for label in ('initial', 'replacement'):
            owner = Owner(python, 'amphora_campaign_runtime', config_path, env, token, output)
            try:
                observed = owner.call('GET', path)
                assert observed == winner, 'Retained authoritative decision changed'
                records.append({'label': label, 'pid': owner.process.pid, 'endpoint': owner.endpoint,
                    'reference': reference, 'kind': winner['outcome']['kind'],
                    'decision_sha256': hashlib.sha256(json.dumps(observed, sort_keys=True).encode()).hexdigest()})
            finally:
                owner.close()
    evidence = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
        'scope': 'Current isolated Runtime HTTP reads of retained immutable winners; same wheel process replacement; '
                 'no migration, mutation, provider call or available peer service required',
        'installation': json.loads((output / 'installation/manifest.json').read_text()), 'reads': records}
    (output / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(f'Verified {len(records)} isolated retained decision reads')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--retained', required=True, nargs='+', type=Path)
    args = parser.parse_args()
    verify(args.output.absolute(), [path.absolute() for path in args.retained])
