"""Actual isolated Knowledge read origin, pinned history and grant failures."""

import argparse
import copy
import json
import os
import secrets
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from planning_knowledge_fixture import ROOT, KnowledgeHost, rescope, task_file
from postgres_fixture import owned_state
from sqlalchemy import URL


def verify(output, installation, knowledge_python):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1', 'Explicit retained PostgreSQL opt-in required'
    output, installation, knowledge_python = output.absolute(), installation.absolute(), knowledge_python.absolute()
    assert json.loads((installation / 'manifest.json').read_bytes())['status'] == 'passed'
    output.mkdir(parents=True, exist_ok=False)
    state = owned_state()
    host, port = state['endpoint'].split(':')
    url = URL.create('postgresql+psycopg', username='knowledge_service', password=state['password'],
                     host=host, port=int(port), database=state['database'])
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment['PYTHONUTF8'] = '1'
    scope = {'tenant_id': 'planning-knowledge-read', 'project_id': uuid.uuid4().hex}
    fixture = json.loads((ROOT / 'services/knowledge/tests/fixtures/initial.json').read_bytes())
    rescope(fixture, scope)
    fixture_path = output / 'synthetic-owner-fixture.json'
    fixture_path.write_text(json.dumps(fixture), encoding='utf-8')
    seed_env = dict(environment, PLANNING_KNOWLEDGE_DATABASE=url.render_as_string(hide_password=False))

    def run(python, args, env):
        result = subprocess.run([str(python), '-I', *map(str, args)], cwd=output, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', timeout=45)
        with (output / 'processes.log').open('a', encoding='utf-8') as log:
            log.write(result.stdout)
        assert result.returncode == 0, 'Knowledge read acceptance process failed; inspect processes.log'
        return json.loads(result.stdout)

    seed = ROOT / 'dev/planning_knowledge_seed.py'
    first = run(knowledge_python, [seed, 'prepare', fixture_path], seed_env)
    token, denied = secrets.token_hex(32), secrets.token_hex(32)
    config = {'database_url_env': 'PLANNING_KNOWLEDGE_DATABASE', 'principals': [
        {'token_env': 'PLANNING_KNOWLEDGE_TOKEN', 'actor_id': 'fixture', 'scope': scope, 'actions': ['read_graph']},
        {'token_env': 'PLANNING_KNOWLEDGE_DENIED', 'actor_id': 'denied', 'scope': scope, 'actions': ['propose_graph']}],
        'vocabulary': first['profile']['vocabulary'], 'policy': first['policy_definition'],
        'data': {'endpoint': 'http://127.0.0.1:1', 'token_env': 'PLANNING_KNOWLEDGE_TOKEN'},
        'research': {'endpoint': 'http://127.0.0.1:1', 'token_env': 'PLANNING_KNOWLEDGE_TOKEN'}}
    config_path = output / 'knowledge.json'
    config_path.write_text(json.dumps(config), encoding='utf-8')
    host_env = dict(seed_env, PLANNING_KNOWLEDGE_TOKEN=token, PLANNING_KNOWLEDGE_DENIED=denied)
    historical = task_file(output / 'historical.json', copy.deepcopy(first))
    genesis = task_file(output / 'genesis.json', copy.deepcopy(first), genesis=True)
    foreign = task_file(output / 'foreign.json', copy.deepcopy(first), scope=dict(scope, project_id='foreign'))
    missing = task_file(output / 'missing.json', copy.deepcopy(first), unavailable=True)
    probe = output / 'knowledge_read_probe.py'
    shutil.copyfile(ROOT / 'services/agent_planning/tests/acceptance/knowledge_read_probe.py', probe)
    owner = KnowledgeHost(knowledge_python, config_path, host_env)
    owner_pids, records = [owner.process.pid], {}

    def read(label, path, credential=token, python=None):
        record = run(python or installation / 'replacement/Scripts/python.exe', [probe, path],
            dict(environment, PLANNING_KNOWLEDGE_ENDPOINT=owner.endpoint, PLANNING_KNOWLEDGE_TOKEN=credential))
        records[label] = record
        return record

    try:
        original = read('original', historical, python=installation / 'initial/Scripts/python.exe')
        assert original['status'] == 'read' and original['calls'] == 3
        assert original['snapshot'] == first['head']['snapshot']
        discovery = read('genesis', genesis)
        assert discovery['status'] == 'read' and discovery['calls'] == 1 and discovery['snapshot'] is None
        second = run(knowledge_python, [seed, 'advance', fixture_path], seed_env)
        assert second['head']['snapshot']['revision'] == first['head']['snapshot']['revision'] + 1
        after = read('after-new-head', historical)
        assert after['snapshot_sha256'] == original['snapshot_sha256']
        owner.close()
        owner = KnowledgeHost(knowledge_python, config_path, host_env)
        owner_pids.append(owner.process.pid)
        restored = read('after-owner-restart', historical)
        assert restored['snapshot_sha256'] == original['snapshot_sha256'] and restored['profile_sha256'] == original['profile_sha256']
        future = read('future-campaign', task_file(output / 'future.json', copy.deepcopy(second)))
        assert future['snapshot'] == second['head']['snapshot'] and future['snapshot_sha256'] != original['snapshot_sha256']
        assert read('read-grant-denied', historical, denied)['status'] == 'knowledge_access_denied'
        assert read('foreign-scope', foreign)['status'] == 'knowledge_access_denied'
        assert read('missing-exact-revision', missing)['status'] == 'knowledge_reference_unavailable'
    finally:
        owner.close()
    assert len({row['pid'] for row in records.values()}) == len(records)
    manifest = {'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'planning': '0.18.0', 'knowledge': '0.17.0', 'knowledge_contracts': '0.8.0',
        'knowledge_host_pids': owner_pids, 'knowledge_fixture_pids': [first['pid'], second['pid']],
        'planning_processes': records,
        'limits': ['Synthetic owner-local accepted input fixture; no real source rights or Planning proposal acceptance',
                   'Actual public authenticated reads, owner PostgreSQL and two host processes; Data/Research offline',
                   'No live model or scientific validity claim; accepted Planning proposal replay remains B2.03']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'planning_processes': len(records), 'knowledge_hosts': len(owner_pids)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--installation', type=Path, required=True)
    parser.add_argument('--knowledge-python', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.installation, args.knowledge_python)
