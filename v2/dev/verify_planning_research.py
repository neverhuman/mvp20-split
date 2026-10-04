"""Installed Planning consumes immutable Research questions without peer imports."""

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

from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_contracts_core import Scope
from amphora_contracts_planning import extraction_draft_schema
from planning_knowledge_fixture import ROOT, ReadOwnerHost, rescope
from postgres_fixture import owned_state
from sqlalchemy import URL


def task_file(path, template, references, scope):
    value = copy.deepcopy(template)
    rescope(value, scope)
    request, task = value['request'], value['task']
    request['context']['output_schema'] = extraction_draft_schema().model_dump(mode='json')
    task['known_questions'] = copy.deepcopy(references)
    rescope(task['known_questions'], scope)
    bound = RequestSnapshot.from_bytes(json.dumps(request).encode(), actor_id=request['actor_id'],
                                      scope=Scope.model_validate_json(json.dumps(scope)))
    task['request_sha256'] = bound.sha256
    ExtractionSnapshot.from_bytes(json.dumps(task).encode(), bound)
    path.write_text(json.dumps({'request': request, 'task': task}), encoding='utf-8')
    return path


def verify(output, installation, research_python):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1', 'Explicit retained PostgreSQL opt-in required'
    output, installation, research_python = output.absolute(), installation.absolute(), research_python.absolute()
    assert json.loads((installation / 'manifest.json').read_bytes())['status'] == 'passed'
    output.mkdir(parents=True, exist_ok=False)
    state = owned_state()
    host, port = state['endpoint'].split(':')
    url = URL.create('postgresql+psycopg', username='research_service', password=state['password'],
                     host=host, port=int(port), database=state['database'])
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment['PYTHONUTF8'] = '1'
    scope = {'tenant_id': 'planning-research-read', 'project_id': uuid.uuid4().hex}
    template = json.loads((ROOT / 'services/agent_planning/tests/extraction/fixtures/extraction.json').read_bytes())
    rescope(template, scope)
    question = {'wire_version': '1', 'reference': {'scope': scope, 'question_id': 'q', 'revision': 1},
        'objective': 'Original synthetic question', 'applicability': template['request']['context']['objective'],
        'criteria': [{'criterion_id': 'c', 'description': 'Explicit criterion'}], 'supersedes': None}
    fixture = output / 'synthetic-owner-question.json'
    fixture.write_text(json.dumps(question), encoding='utf-8')
    seed_env = dict(environment, PLANNING_RESEARCH_DATABASE=url.render_as_string(hide_password=False))

    def run(python, args, env):
        result = subprocess.run([str(python), '-I', *map(str, args)], cwd=output, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', timeout=45)
        with (output / 'processes.log').open('a', encoding='utf-8') as log:
            log.write(result.stdout)
        assert result.returncode == 0, 'Research read acceptance process failed; inspect processes.log'
        return json.loads(result.stdout)

    seed = ROOT / 'dev/planning_research_seed.py'
    first = run(research_python, [seed, 'prepare', fixture], seed_env)
    token, denied = secrets.token_hex(32), secrets.token_hex(32)
    config = {'database_url_env': 'PLANNING_RESEARCH_DATABASE', 'principals': [
        {'token_env': 'PLANNING_RESEARCH_TOKEN', 'actor_id': 'fixture', 'scope': scope, 'actions': ['read_declarations']},
        {'token_env': 'PLANNING_RESEARCH_DENIED', 'actor_id': 'denied', 'scope': scope, 'actions': ['resolve_identity']}]}
    config_path = output / 'research.json'
    config_path.write_text(json.dumps(config), encoding='utf-8')
    host_env = dict(seed_env, PLANNING_RESEARCH_TOKEN=token, PLANNING_RESEARCH_DENIED=denied)
    historical = task_file(output / 'historical.json', template, [question['reference']], scope)
    foreign = task_file(output / 'foreign.json', template, [question['reference']], dict(scope, project_id='foreign'))
    mixed = task_file(output / 'mixed.json', template,
        [dict(question['reference'], question_id='missing'), question['reference']], scope)
    probe = output / 'research_read_probe.py'
    shutil.copyfile(ROOT / 'services/agent_planning/tests/acceptance/research_read_probe.py', probe)
    owner = ReadOwnerHost(research_python, config_path, host_env, module='amphora_research')
    owner_pids, records = [owner.process.pid], {}

    def read(label, path, credential=token, python=None):
        record = run(python or installation / 'replacement/Scripts/python.exe', [probe, path],
            dict(environment, PLANNING_RESEARCH_ENDPOINT=owner.endpoint, PLANNING_RESEARCH_TOKEN=credential))
        records[label] = record
        return record

    try:
        original = read('original', historical, python=installation / 'initial/Scripts/python.exe')
        assert original['records'] == [question] and original['calls'] == 1 and not original['gaps']
        second = run(research_python, [seed, 'advance', fixture], seed_env)
        after = read('after-new-revision', historical)
        assert after['records'] == original['records'] and after['record_sha256'] == original['record_sha256']
        owner.close()
        owner = ReadOwnerHost(research_python, config_path, host_env, module='amphora_research')
        owner_pids.append(owner.process.pid)
        restored = read('after-owner-restart', historical)
        assert restored['records'] == original['records'] and restored['record_sha256'] == original['record_sha256']
        future = read('future-campaign', task_file(output / 'future.json', template, [second['question']['reference']], scope))
        assert future['records'] == [second['question']] and future['record_sha256'] != original['record_sha256']
        for label, path, credential in [('grant-denied', historical, denied), ('foreign-scope', foreign, token)]:
            result = read(label, path, credential)
            assert not result['records'] and {gap['reason'] for gap in result['gaps']} == {'research_access_denied'}
        partial = read('missing-plus-available', mixed)
        assert partial['records'] == [question] and partial['calls'] == 2
        assert [gap['reason'] for gap in partial['gaps']] == ['research_reference_unavailable']
        owner.close()
        unavailable = read('owner-offline', historical)
        assert not unavailable['records'] and [gap['reason'] for gap in unavailable['gaps']] == ['research_peer_unavailable']
    finally:
        owner.close()
    assert len({row['pid'] for row in records.values()}) == len(records)
    manifest = {'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'planning': '0.20.0', 'research': '0.33.0', 'research_contracts': '0.14.0',
        'research_host_pids': owner_pids, 'research_fixture_pids': [first['pid'], second['pid']],
        'planning_processes': records,
        'limits': ['Synthetic Research-local question publication; no production declaration-write API or Data rights proof',
                   'Actual authenticated immutable reads, retained owner PostgreSQL, two host processes; Data/Knowledge offline',
                   'No provider/model/scientific acceptance; Planning proposal submission remains B2.03']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'planning_processes': len(records), 'research_hosts': len(owner_pids)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--installation', type=Path, required=True)
    parser.add_argument('--research-python', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.installation, args.research_python)
