"""Fresh output-profile installations, predecessor vectors and durable process replay."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import URL

from build_tool_images import closure
from check_boundaries import ROOT, project_specs
from postgres_fixture import owned_state, planning_owner


def fixtures(tests):
    from amphora_contracts_planning import campaign_draft_schema

    result = []
    base = json.loads((tests / 'context/fixtures/request.json').read_bytes())
    for name in ('future', 'adjustment', 'evidence', 'abstain'):
        request = json.loads(json.dumps(base))
        draft = json.loads((tests / f'campaign_output/fixtures/{name}.json').read_bytes())
        request.update(purpose='supervision' if name == 'adjustment' else 'campaign_proposal',
                       decision_scope=draft['decision_scope'],
                       runtime_cut=draft['candidate']['cut'] if name == 'adjustment' else None)
        request['context']['output_schema'] = campaign_draft_schema().model_dump(mode='json')
        request['context']['allowed_actions'] = ['abstain', 'request_evidence', 'propose_campaign']
        result.append({'name': name, 'request': request, 'draft': draft,
                       'status': 'abstained' if name == 'abstain' else 'proposed'})
    legacy = json.loads((tests / 'providers/fixtures/legacy-observation-v1.json').read_bytes())
    old = json.loads((tests / 'campaign_output/fixtures/predecessor-extraction.json').read_bytes())['cases']
    for name, case in [('reference', legacy), *((item['name'], item) for item in old)]:
        result.append({'name': name, 'request': case['request'],
                       'draft': json.loads(case['capture_utf8']), 'status': 'proposed'})
    scope = {'tenant_id': 'planning-output-replacement', 'project_id': uuid.uuid4().hex}

    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {'tenant_id', 'project_id'}:
                value.update(scope)
            for child in value.values():
                rescope(child)
        elif isinstance(value, list):
            for child in value:
                rescope(child)

    for index, case in enumerate(result):
        rescope(case)
        case['request']['reference']['engagement_id'] = 'output-' + str(index)
        case['capture_utf8'] = json.dumps(case.pop('draft'), indent=2)
    return result


def verify(output):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1', 'Explicit retained PostgreSQL opt-in required'
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    wheels = output / 'wheels'
    wheels.mkdir()
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith('AMPHORA_') and key != 'PYTHONPATH'}
    environment['PYTHONUTF8'] = '1'
    uv = ROOT / ('.venv/Scripts/uv.exe' if os.name == 'nt' else '.venv/bin/uv')
    specs = {cfg['project']['name']: (path, cfg, module) for path, cfg, module in project_specs()}
    assert specs['amphora-agent-planning'][1]['project']['version'] == '0.52.0', 'Review migration compatibility before reuse'

    def run(arguments, *, env=environment, expected=0, log='build.log'):
        result = subprocess.run([str(arg) for arg in arguments], cwd=output, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding='utf-8', timeout=120, check=False)
        with (output / log).open('a', encoding='utf-8') as stream:
            stream.write(result.stdout)
        assert result.returncode == expected, f'Campaign output verification failed; inspect {output / log}'

    for name in sorted(closure('amphora-agent-planning', specs)):
        run([uv, 'build', '--project', specs[name][0], '--wheel', '--out-dir', wheels])
    pythons = {}
    for name in ('initial', 'replacement'):
        location = output / name
        run([uv, 'venv', '--python', sys.executable, location])
        python = location / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        run([uv, 'pip', 'install', '--python', python, *sorted(wheels.glob('*.whl')), 'pytest>=8,<9', 'jsonschema>=4,<5'])
        run([python, '-I', '-c', "import sys,importlib.util;from pathlib import Path;from importlib.metadata import version;"
            "import amphora_agent_planning;assert version('amphora-agent-planning')=='0.52.0';"
            "assert version('amphora-contracts-planning')=='0.9.0';"
            "assert Path(amphora_agent_planning.__file__).absolute().is_relative_to(Path(sys.prefix).absolute());"
            "assert all(importlib.util.find_spec(n) is None for n in ('amphora_research','amphora_knowledge',"
            "'amphora_campaign_runtime','amphora_data_artifacts','amphora_capability_registry','fastapi'))"])
        pythons[name] = python
    for source, destination in [('services/agent_planning/tests', 'tests/service'),
                                ('contracts/planning/tests', 'tests/contracts'), ('contracts/commands/tests', 'tests/commands')]:
        shutil.copytree(ROOT / source, output / destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    config = output / 'pytest.ini'
    config.write_text('[pytest]\naddopts = --import-mode=importlib\nmarkers =\n    postgres: opt-in owned PostgreSQL\n', encoding='utf-8')
    pure = [output / 'tests/contracts', output / 'tests/commands',
            *(output / 'tests/service' / name for name in ('campaign_output', 'providers', 'persistence/test_records.py'))]
    run([pythons['initial'], '-I', '-m', 'pytest', '-c', config, *pure, '-q', '--tb=short',
         '--junitxml=' + str(output / 'pure.xml')], log='tests.log')
    state = owned_state()
    planning_owner(state)
    host, port = state['endpoint'].split(':')
    migrator = URL.create('postgresql+psycopg', username='planning_migrator', password=state['password'],
                         host=host, port=int(port), database=state['database'])
    sql_environment = {**environment, 'AMPHORA_TEST_POSTGRES': '1',
        'AMPHORA_TEST_PLANNING_MIGRATOR_URL': migrator.render_as_string(hide_password=False),
        'AMPHORA_TEST_PLANNING_SERVICE_URL': migrator.set(username='planning_service').render_as_string(hide_password=False)}
    sql = [output / 'tests/service' / name for name in ('campaign_output_storage',
           'persistence/test_task_output.py', 'persistence/test_edit_profiles.py')]
    run([pythons['initial'], '-I', '-m', 'pytest', '-c', config, *sql, '-q', '--tb=short',
         '--junitxml=' + str(output / 'sql.xml')], env=sql_environment, log='tests.log')
    counts = {}
    for name in ('pure', 'sql'):
        suites = ET.parse(output / (name + '.xml')).getroot().findall('testsuite')
        assert suites and all(int(row.attrib[key]) == 0 for row in suites for key in ('errors', 'failures', 'skipped'))
        counts[name] = {'tests': sum(int(row.attrib['tests']) for row in suites),
                        'seconds': sum(float(row.attrib['time']) for row in suites)}
    fixture = output / 'fixture.json'
    fixture.write_text(json.dumps(fixtures(output / 'tests/service'), indent=2) + '\n', encoding='utf-8')
    stages = [('initial', 'absent', 0), ('initial', 'commit-crash', 91), ('initial', 'recover', 0),
              ('replacement', 'read', 0), ('replacement', 'replay', 0), ('initial', 'read', 0)]
    for name, stage, expected in stages:
        run([pythons[name], '-I', output / 'tests/service/acceptance/campaign_output_probe.py', stage,
             '--fixture', fixture, '--expected', output / 'retained.json'], env=sql_environment,
            expected=expected, log='workers.log')
    manifest = {'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'planning': '0.52.0', 'contracts': '0.9.0', 'migration': 'planning0012',
        'installations': 2, 'tests': counts,
        'stages': [{'installation': name, 'stage': stage, 'exit_code': code} for name, stage, code in stages],
        'retained': json.loads((output / 'retained.json').read_bytes()),
        'wheels': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(wheels.glob('*.whl'))},
        'limits': ['Two installations of same implementation; no rewrite or real-provider/scientific claim',
                   'Current forward migration only, no reset/history mutation; credentials environment-only',
                   'Literal reference and extraction predecessor vectors plus unchanged numeric command vectors']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'tests': counts, 'installations': 2, 'worker_stages': len(stages)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    verify(parser.parse_args().output)
