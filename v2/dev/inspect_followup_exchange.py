"""Read retained failed follow-up run through its isolated Runtime; never advance or reset."""

import argparse
import json
import os
import secrets
from pathlib import Path

from sqlalchemy import URL

from campaign_context_fixture.support import environment
from postgres_fixture import owned_state
from supervision_owner_fixture.hosts import Owner
from followup_acceptance.materials import write


def inspect(installation, source):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1'
    installation, source = installation.absolute(), source.absolute()
    manifest = json.loads((installation / 'manifest.json').read_bytes())
    receipt = json.loads((source / 'graph.admit_supervised-receipt.json').read_bytes())
    run = receipt['outcome']['committed']['object_id']
    state = owned_state(); host, port = state['endpoint'].split(':')
    database = URL.create('postgresql+psycopg', username='runtime_service', password=state['password'],
        host=host, port=int(port), database=state['database']).render_as_string(hide_password=False)
    token = secrets.token_hex(32)
    configuration = json.loads((source / 'runtime.json').read_bytes())
    configuration['inspection'] = {'cursor_key_env': 'PROOF_CURSOR_KEY'}
    config = write(source / 'readback-runtime.json', configuration)
    owner = Owner(Path(manifest['owners']['runtime']['python']), 'amphora_campaign_runtime', config,
        {**environment(), 'PROOF_DATABASE_URL': database, 'PROOF_OWNER_TOKEN': token, 'PROOF_DATA_TOKEN': secrets.token_hex(32),
         'PROOF_CURSOR_KEY': secrets.token_hex(32)}, token, source)
    try:
        graph = owner.call('GET', '/v3/graph-runs/' + run)
        write(source / 'failure-graph.json', graph)
        checkpoints = owner.call('GET', '/v1/supervision/runs/' + run + '/checkpoints?limit=10')
        decisions = [owner.call('GET', '/v1/supervision/decisions/' + run + '/' + row['reference']['decision_id']) for row in checkpoints['items']]
        write(source / 'failure-readback.json', {'graph': graph, 'checkpoints': checkpoints, 'decisions': decisions})
        print(json.dumps({'run_id': run, 'status': graph['status'], 'checkpoints': len(decisions),
                          'outcomes': [row['outcome']['kind'] for row in decisions]}))
    finally:
        owner.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installation', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args(); inspect(args.installation, args.source)
