"""Public reconstruction plus independent consumer install and actual owner replacement."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
from pathlib import Path
from unittest.mock import patch

import qdrant_fixture
from verify_studio import stage_source

from .consumer import verify
from .process import base_environment


def rejected(owner, path, body, expected):
    try:
        owner.request(path, body)
    except urllib.error.HTTPError as error:
        assert error.code == expected
        return {'status': error.code, 'response': json.load(error)}
    raise AssertionError('Missing physical index was silently promoted')


def prove(scenario, records, output):
    output.mkdir(parents=True)
    heads = [records['head']]
    if records.get('feedback'):
        heads.append(records['feedback']['proposal']['decision']['decision']['head'])
    if records.get('races'):
        heads.extend(item['result']['decision']['head'] for item in records['races']['proposals'] if item['result']['decision']['outcome'] == 'accepted')
    snapshots = [scenario.knowledge.request('/v1/graph-snapshots/read', head['snapshot']) for head in heads]
    scenario.data.close()
    request = {'wire_version': '1', 'graph': records['proposal']['graph'], 'rebuild_id': 'independent-reconstruction'}
    rebuilt = scenario.knowledge.request('/v1/graph-rebuilds', request)
    assert rebuilt['result']['outcome'] == 'published' and rebuilt['result']['head'] == heads[-1]
    assert [scenario.knowledge.request('/v1/graph-snapshots/read', head['snapshot']) for head in heads] == snapshots
    processes = {'knowledge': scenario.replace('knowledge'), 'research': scenario.replace('research')}
    assert scenario.knowledge.request('/v1/graph-rebuilds/read', request) == rebuilt
    assert [scenario.knowledge.request('/v1/graph-snapshots/read', head['snapshot']) for head in heads] == snapshots
    with patch.object(qdrant_fixture, 'STATE', qdrant_fixture.ROOT / '.test-results/qdrant-replacement-fixture.json'):
        backend = qdrant_fixture.owned_state()
    config = json.loads((scenario.directory / 'data_artifacts.json').read_text(encoding='utf-8'))
    primary_endpoint = config['retrieval']['endpoint']
    primary_token = scenario.environments['data_artifacts']['QDRANT_TOKEN']
    assert config['retrieval']['endpoint'] != backend['endpoint']
    config['retrieval']['endpoint'] = backend['endpoint']
    scenario.environments['data_artifacts']['QDRANT_TOKEN'] = backend['api_key']
    processes['data'] = scenario.replace('data_artifacts', config=config)
    original = records['representation']
    assert scenario.data.request('/v1/retrieval/queries/baseline') == original['query']
    old_query = {'wire_version': '1', 'retrieval_id': 'absent-projection', 'generation': original['generation']['generation']['reference'],
        'query': original['binding']['reference'], 'policy': original['query']['policy']}
    missing = rejected(scenario.data, '/v1/retrieval/queries', old_query, 503)
    pending = rejected(scenario.data, '/v1/retrieval/queries/absent-projection', None, 409)
    generation_request = {'wire_version': '1', 'corpus_id': 'feedback', 'generation_id': 'independently-rebuilt',
        'profile': original['profile'], 'bindings': [original['binding']['reference']],
        'expected_head': original['generation']['generation']['reference']}
    generation = scenario.data.request('/v1/retrieval/generations', generation_request)
    assert generation['state'] == 'published'
    assert generation['generation']['reference'] != original['generation']['generation']['reference']
    query = {**old_query, 'retrieval_id': 'independently-rebuilt', 'generation': generation['generation']['reference']}
    result = scenario.data.request('/v1/retrieval/queries', query)
    assert result['matches'] == original['query']['matches']
    assert scenario.data.request('/v1/retrieval/queries/baseline') == original['query']
    assert scenario.data.request('/v1/retrieval/generations', generation_request) == generation
    assert scenario.data.request('/v1/retrieval/queries', query) == result
    config['retrieval']['endpoint'] = primary_endpoint
    scenario.environments['data_artifacts']['QDRANT_TOKEN'] = primary_token
    processes['data_recovery'] = scenario.replace('data_artifacts', config=config)
    recovered = scenario.data.request('/v1/retrieval/queries', old_query)
    assert recovered['matches'] == original['query']['matches']
    assert scenario.data.request('/v1/retrieval/queries', old_query) == recovered
    assert scenario.data.request('/v1/retrieval/queries/absent-projection') == recovered
    config['retrieval']['endpoint'] = backend['endpoint']
    scenario.environments['data_artifacts']['QDRANT_TOKEN'] = backend['api_key']
    processes['data_final'] = scenario.replace('data_artifacts', config=config)
    fresh = scenario.data.request('/v1/retrieval/queries', {**query, 'retrieval_id': 'after-owner-replacement'})
    assert fresh['matches'] == original['query']['matches']
    assert scenario.data.request('/v1/retrieval/queries/absent-projection') == recovered
    with tempfile.TemporaryDirectory(prefix='amphora-feedback-consumer-') as temporary:
        workspace = Path(temporary).resolve()
        assert workspace.is_relative_to(Path(tempfile.gettempdir()).resolve())
        studio, copied, schemas = stage_source(workspace)
        npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
        assert npm is not None
        outputs = {}
        for name, command in [('install', [npm, 'ci', '--ignore-scripts', '--no-audit', '--no-fund']),
                              ('verify', ['node', 'scripts/verify.mjs', '--coverage'])]:
            process = subprocess.run(command, cwd=studio, env=base_environment(), capture_output=True,
                text=True, encoding='utf-8', timeout=180, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            outputs[name] = process.stdout + process.stderr
            (output / (name + '.log')).write_text(outputs[name], encoding='utf-8')
            assert process.returncode == 0, 'Independent Studio ' + name + ' failed; see retained log'
        count = re.search(r'(?:tests|pass)\s+(\d+)', outputs['verify'])
        assert count is not None
        manifest = {'source_sha256': copied, 'public_schema_pins': schemas, 'tests': int(count.group(1))}
        manifest_path = output / 'consumer-manifest.json'
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        consumer = verify(scenario, records, studio, output / 'browser', browser=True)
    return {'knowledge': rebuilt, 'snapshots_preserved': [head['snapshot'] for head in heads],
        'processes': processes, 'missing_physical_index': missing, 'pending_query': pending,
        'generation': generation, 'retrieval': result, 'recovered_query': recovered, 'fresh_query': fresh,
        'consumer': consumer, 'consumer_tests': manifest['tests'],
        'consumer_manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'limits': ['New explicitly pinned retrieval generation, not same-ID physical rematerialization',
                   'Fresh processes of independently installed owners; separate clean Studio installation',
                   'No power-loss, production gateway, semantic-vector quality or scientific-validity claim']}
