"""Two fresh Planning installations, SQL oracles and lost-acknowledgement recovery."""

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
    assert specs['amphora-agent-planning'][1]['project']['version'] == '0.49.0', 'Review migration compatibility before reusing'

    def run(arguments, *, env=environment, expected=0, log='build.log'):
        result = subprocess.run([str(arg) for arg in arguments], cwd=output, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding='utf-8', timeout=120, check=False)
        with (output / log).open('a', encoding='utf-8') as stream:
            stream.write(result.stdout)
        assert result.returncode == expected, f'Campaign journal worker failed; inspect {output / log}'
        return result.stdout

    for name in sorted(closure('amphora-agent-planning', specs)):
        run([uv, 'build', '--project', specs[name][0], '--wheel', '--out-dir', wheels])
    pythons = {}
    for name in ('initial', 'replacement'):
        location = output / name
        run([uv, 'venv', '--python', sys.executable, location])
        python = location / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        run([uv, 'pip', 'install', '--python', python, *sorted(wheels.glob('*.whl')), 'pytest>=8,<9', 'jsonschema>=4,<5'])
        run([python, '-I', '-c', "import sys,importlib.util;from pathlib import Path;from importlib.metadata import version;"
            "from importlib.resources import files;import amphora_agent_planning;"
            "assert version('amphora-agent-planning')=='0.49.0';"
            "assert Path(amphora_agent_planning.__file__).absolute().is_relative_to(Path(sys.prefix).absolute());"
            "assert files('amphora_agent_planning').joinpath('persistence/migrations/versions/r0012_campaign_preparations.sql').is_file();"
            "assert all(importlib.util.find_spec(n) is None for n in ('amphora_research','amphora_knowledge',"
            "'amphora_campaign_runtime','amphora_data_artifacts','amphora_capability_registry','fastapi'))"])
        pythons[name] = python
    shutil.copytree(ROOT / 'services/agent_planning/tests', output / 'tests', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    config = output / 'pytest.ini'
    config.write_text('[pytest]\naddopts = --import-mode=importlib\nmarkers =\n    postgres: opt-in owned PostgreSQL\n', encoding='utf-8')
    state = owned_state()
    planning_owner(state)
    host, port = state['endpoint'].split(':')
    migrator = URL.create('postgresql+psycopg', username='planning_migrator', password=state['password'],
        host=host, port=int(port), database=state['database'])
    sql_environment = {**environment, 'AMPHORA_TEST_POSTGRES': '1',
        'AMPHORA_TEST_PLANNING_MIGRATOR_URL': migrator.render_as_string(hide_password=False),
        'AMPHORA_TEST_PLANNING_SERVICE_URL': migrator.set(username='planning_service').render_as_string(hide_password=False)}
    # The current installed migrator runs twice via planning_database. Never use an old installation here.
    run([pythons['initial'], '-I', '-m', 'pytest', '-c', config, output / 'tests/campaign_preparation_storage',
         '-q', '--tb=short', '--junitxml=' + str(output / 'tests.xml')], env=sql_environment, log='tests.log')
    suites = ET.parse(output / 'tests.xml').getroot().findall('testsuite')
    count = sum(int(row.attrib['tests']) for row in suites)
    assert count == 23 and all(int(row.attrib[key]) == 0 for row in suites for key in ('errors', 'failures', 'skipped'))
    value = json.loads((output / 'tests/campaign_packet/fixtures/predecessor-v1.json').read_bytes())
    scope = {'tenant_id': 'planning-campaign-replacement', 'project_id': uuid.uuid4().hex}

    def rescope(item):
        if isinstance(item, dict):
            if set(item) == {'tenant_id', 'project_id'}:
                item.update(scope)
            for child in item.values():
                rescope(child)
        elif isinstance(item, list):
            for child in item:
                rescope(child)

    rescope(value['request'])
    fixture = output / 'fixture.json'
    fixture.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    worker = output / 'tests/acceptance/campaign_preparation_probe.py'
    stages = [('initial', 'absent', 0), ('initial', 'commit-crash', 91), ('initial', 'recover', 0),
              ('replacement', 'read', 0), ('replacement', 'replay', 0), ('replacement', 'conflict', 0), ('initial', 'read', 0)]
    for name, stage, expected in stages:
        run([pythons[name], '-I', worker, stage, '--fixture', fixture, '--loader', output / 'tests/campaign_packet/replay_probe.py',
             '--expected', output / 'retained.json'], env=sql_environment, expected=expected, log='workers.log')
    manifest = {'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'planning': '0.49.0', 'migration': 'planning0012', 'installations': 2,
        'sql_tests': count, 'sql_seconds': sum(float(row.attrib['time']) for row in suites),
        'stages': [{'installation': name, 'stage': stage, 'exit_code': code} for name, stage, code in stages],
        'retained': json.loads((output / 'retained.json').read_bytes()),
        'wheels': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(wheels.glob('*.whl'))},
        'limits': ['Same implementation in two installations, not a fresh rewrite',
                   'Synthetic retained SQL scope only; no source rights, actual peer owners, provider or science claim',
                   'No reset/history rewrite; current forward migrator only; credentials environment-only']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'sql_tests': count, 'installations': 2, 'worker_stages': len(stages)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    verify(parser.parse_args().output)
