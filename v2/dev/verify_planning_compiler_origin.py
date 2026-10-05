"""Run scoped compiler SQL tests in an already verified current Planning installation."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tomllib
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import URL

from postgres_fixture import owned_state, planning_owner

ROOT = Path(__file__).absolute().parents[1]


def verify(installation, output, area='origin'):
    areas = {'origin': ('campaign_handoff_storage',), 'coordinator': ('campaign_dispatch_coordinator',),
             'selection': ('campaign_handoff_storage', 'campaign_dispatch_storage')}
    if area not in areas:
        raise ValueError('Unknown compiler SQL area')
    installation, output = installation.absolute(), output.absolute()
    if output.exists():
        raise ValueError('Use a fresh SQL evidence directory')
    source = json.loads((installation / 'manifest.json').read_text(encoding='utf-8'))
    current = tomllib.loads((ROOT / 'services/agent_planning/pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    if source['status'] != 'passed' or source['planning'] != current or source['scope'] not in {'compiler', 'dispatch'}:
        raise ValueError('Require a passed current compiler wheel verification; never run an old migrator')
    python = installation / ('environment/Scripts/python.exe' if os.name == 'nt' else 'environment/bin/python')
    output.mkdir(parents=True)
    state = owned_state()
    planning_owner(state)
    host, port = state['endpoint'].split(':')
    url = URL.create('postgresql+psycopg', username='planning_migrator', password=state['password'],
                     host=host, port=int(port), database=state['database'])
    environment = {key: value for key, value in os.environ.items() if not key.startswith('AMPHORA') and key != 'PYTHONPATH'}
    environment.update(PYTHONUTF8='1', AMPHORA_TEST_POSTGRES='1',
        AMPHORA_TEST_PLANNING_MIGRATOR_URL=url.render_as_string(hide_password=False),
        AMPHORA_TEST_PLANNING_SERVICE_URL=url.set(username='planning_service').render_as_string(hide_password=False))

    def run(arguments):
        result = subprocess.run([str(item) for item in arguments], cwd=output, env=environment,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', timeout=120)
        with (output / 'tests.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout)
        if result.returncode:
            raise RuntimeError('Installed compiler SQL verification failed; inspect retained tests.log')

    run([python, '-I', '-c', "import importlib.metadata as m; assert m.version('amphora-agent-planning') == " + repr(current)])
    files = [path for name in areas[area] for path in sorted((installation / 'tests/service' / name).rglob('test_*.py'))]
    assert files, 'Require copied module-owned SQL tests'
    suites = []
    for index, path in enumerate(files):
        report = output / f'tests-{index}.xml'
        run([python, '-I', '-m', 'pytest', path, '--import-mode=importlib', '--tb=short', '-q', '--junitxml=' + str(report)])
        suites.extend(ET.parse(report).getroot().findall('testsuite'))
    aggregate = ET.Element('testsuites')
    aggregate.extend(suites)
    ET.ElementTree(aggregate).write(output / 'tests.xml', encoding='utf-8', xml_declaration=True)
    count = sum(int(suite.attrib['tests']) for suite in suites)
    assert count > 0 and all(int(suite.attrib[key]) == 0 for suite in suites for key in ('errors', 'failures', 'skipped'))
    manifest = {'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'planning': current, 'area': area, 'tests': count, 'processes': len(files),
        'seconds': sum(float(suite.attrib['time']) for suite in suites),
        'installation_manifest': str(installation / 'manifest.json'),
        'limits': ['Actual retained Planning PostgreSQL; current package migrations only, no reset',
                   'Existing fresh wheel installation; origin read replacement uses another engine, not a process-kill proof',
                   'No actual Runtime/Registry acceptance, provider or scientific claim']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'tests': count, 'planning': current}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--area', choices=['origin', 'selection', 'coordinator'], default='origin')
    options = parser.parse_args()
    verify(options.installation, options.output, options.area)
