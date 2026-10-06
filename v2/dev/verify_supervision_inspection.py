"""Installed metadata reads and continuation across Runtime process replacement."""

import argparse
import json
import os
import secrets
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from amphora_contracts_supervision import (
    CheckpointContextPage,
    CheckpointInspectionPage,
    CheckpointRequestPage,
    CheckpointResponsePage,
)
from sqlalchemy import URL

from install_owner_peer import install
from postgres_fixture import owned_state
from supervision_owner_fixture.hosts import Owner
from verify_checkpoint_decision_read import retained_paths


def page(owner, path, model, **query):
    value = owner.call('GET', path + ('?' + urlencode(query) if query else ''))
    return model.model_validate_json(json.dumps(value))


def verify(output, retained):
    python = install(output / 'installation', 'amphora-campaign-runtime',
                     ['amphora_agent_planning', 'amphora_data_artifacts'])
    state = owned_state()
    host, port = state['endpoint'].split(':')
    sql = URL.create('postgresql+psycopg', username='runtime_service', password=state['password'],
        host=host, port=int(port), database=state['database']).render_as_string(hide_password=False)
    records = []
    continued = False
    for index, root in enumerate(retained):
        original = json.loads((root / 'evidence.json').read_text())
        winner = original['winner']
        ref = winner['reference']
        config = retained_paths(json.loads((root / 'runtime.json').read_text()), root)
        token = secrets.token_hex(32)
        config['principals'] = [{'token_env': 'INSPECT_READ_TOKEN', 'actor_id': 'read-proof',
                                'scope': ref['scope'], 'actions': ['read']}]
        config['inspection'] = {'cursor_key_env': 'INSPECT_CURSOR_KEY'}
        env = dict(os.environ, CHECKPOINT_RUNTIME_SQL=sql, INSPECT_READ_TOKEN=token,
                   INSPECT_CURSOR_KEY=secrets.token_hex(32), CHECKPOINT_DATA_TOKEN=secrets.token_hex(32))
        config_path = output / f'configuration-{index}.json'
        config_path.write_text(json.dumps(config), encoding='utf-8')
        base = f"/v1/supervision/runs/{ref['run_id']}/checkpoints"
        requests = base + f"/{ref['decision_id']}/requests"
        initial = None
        first = None
        for label in ('initial', 'replacement'):
            owner = Owner(python, 'amphora_campaign_runtime', config_path, env, token, output)
            try:
                exact = owner.call('GET', f"/v1/supervision/decisions/{ref['run_id']}/{ref['decision_id']}")
                assert exact == winner
                listing = page(owner, base, CheckpointInspectionPage)
                assert listing.total == 1 and listing.items[0].winner_kind == winner['outcome']['kind']
                if initial is None:
                    initial = listing.snapshot
                assert listing.snapshot.epoch == initial.epoch
                query = {'snapshot_token': initial.snapshot_token, 'limit': 1}
                observed = page(owner, requests, CheckpointRequestPage, **query)
                if first is None:
                    first = observed
                assert observed.items == first.items and observed.total == first.total
                items = list(observed.items)
                while observed.next_cursor:
                    observed = page(owner, requests, CheckpointRequestPage,
                                    **query, cursor=observed.next_cursor)
                    items.extend(observed.items)
                assert len(items) == first.total
                if label == 'replacement' and first.next_cursor:
                    continuation = page(owner, requests, CheckpointRequestPage, **query, cursor=first.next_cursor)
                    assert continuation.items == tuple(items[1:2])
                    continued = True
                detail = []
                for item in items:
                    counts = {}
                    for suffix, model in (('context', CheckpointContextPage), ('responses', CheckpointResponsePage)):
                        path = requests + f'/{item.request_sha256}/{suffix}'
                        result = page(owner, path, model, **query)
                        entries = list(result.items)
                        while result.next_cursor:
                            result = page(owner, path, model, **query, cursor=result.next_cursor)
                            entries.extend(result.items)
                        assert len(entries) == result.total
                        counts[suffix] = len(entries)
                    detail.append({'request_sha256': item.request_sha256, 'disposition': item.disposition, **counts})
                records.append({'label': label, 'pid': owner.process.pid, 'reference': ref,
                                'winner_kind': winner['outcome']['kind'], 'requests': detail})
            finally:
                owner.close()
    assert continued, 'A real nonempty continuation must survive replacement'
    evidence = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
                'scope': 'Isolated Runtime metadata HTTP over retained actual-owner histories; fresh ports, '
                         'same SQL/config/key; no migration, writes or peer calls',
                'continuation_survived_replacement': continued,
                'installation': json.loads((output / 'installation/manifest.json').read_text()), 'reads': records}
    (output / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(f'Verified {len(records)} installed inspection passes and retained continuation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--retained', required=True, nargs='+', type=Path)
    args = parser.parse_args()
    verify(args.output.absolute(), [path.absolute() for path in args.retained])
