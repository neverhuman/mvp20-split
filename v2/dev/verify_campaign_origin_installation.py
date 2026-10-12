"""UI-01.07 isolated package tests; actual scientific/browser proof is separate."""
import argparse
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from sqlalchemy import URL
from postgres_fixture import owned_state, planning_owner

ROOT = Path(__file__).absolute().parents[1]


def verify(installation, output, retry_from=None):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1'
    output.mkdir(parents=True, exist_ok=False)
    copied = output / 'root'
    for rel in ('services/agent_planning/tests', 'services/local_gateway/tests',
                'contracts/schemas', 'contracts/fixtures', 'contracts/supervision/tests/fixtures'):
        shutil.copytree(ROOT / rel, copied / rel,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    state = owned_state()
    planning_owner(state)
    host, port = state['endpoint'].split(':')
    url = URL.create('postgresql+psycopg', username='planning_migrator', password=state['password'],
                     host=host, port=int(port), database=state['database'])
    env = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    env.update(PYTHONUTF8='1', AMPHORA_TEST_POSTGRES='1',
               AMPHORA_TEST_PLANNING_MIGRATOR_URL=url.render_as_string(hide_password=False),
               AMPHORA_TEST_PLANNING_SERVICE_URL=url.set(username='planning_service').render_as_string(hide_password=False))

    def run(args):
        result = subprocess.run([str(item) for item in args], cwd=output, env=env,
                                capture_output=True, encoding='utf-8', timeout=600,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        with (output / 'verification.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout + result.stderr)
        assert result.returncode == 0, 'Isolated verification failed; inspect verification.log'

    records = {}
    for owner, rel, groups in (
        ('planning', 'services/agent_planning/tests', ['campaign_origin', 'campaign_dispatch_storage',
         'campaign_dispatch', 'campaign_authoring', 'campaign_dispatch_transport', 'supervision_api']),
        ('gateway', 'services/local_gateway/tests', ['.']),
    ):
        manifest = json.loads((installation / owner / 'manifest.json').read_bytes())
        assert manifest['status'] == 'installed'
        python = installation / owner / 'environment/Scripts/python.exe'
        run([ROOT / '.venv/Scripts/uv.exe', 'pip', 'install', '--python', python,
             'pytest>=8,<9', 'httpx>=0.28,<1'])
        tests = copied / rel
        xml = output / (owner + '.xml')
        if retry_from is not None and owner == 'planning':
            previous = ET.parse(retry_from / 'planning.xml').getroot().findall('.//testcase')
            failures = [case for case in previous if case.find('failure') is not None or case.find('error') is not None]
            assert failures and all('.supervision_api.' in case.attrib['classname'] for case in failures)
            groups = ['supervision_api']
        arguments = [str(tests / group) for group in groups] + [
            '--confcutdir=' + str(tests), '--import-mode=importlib', '-q', '--tb=short', '--junitxml=' + str(xml)]
        run([python, '-I', '-c', 'import pytest; raise SystemExit(pytest.main(' + repr(arguments) + '))'])
        suites = ET.parse(xml).getroot().findall('testsuite')
        assert suites and all(int(s.attrib[key]) == 0 for s in suites for key in ('errors', 'failures', 'skipped'))
        count = sum(int(s.attrib['tests']) for s in suites)
        if retry_from is not None and owner == 'planning':
            current = {(case.attrib['classname'], case.attrib['name']) for case in ET.parse(xml).getroot().findall('.//testcase')}
            assert all((case.attrib['classname'], case.attrib['name']) in current for case in failures)
            assert all(case.find('skipped') is None for case in previous)
            count = len({(case.attrib['classname'], case.attrib['name']) for case in previous} | current)
        records[owner] = {'tests': count, 'installation': manifest}
        print(json.dumps({'owner': owner, 'tests': records[owner]['tests'], 'status': 'passed'}), flush=True)
    evidence = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
                'owners': records, 'prior_attempt': None if retry_from is None else str(retry_from),
                'limits': ['Independent wheels and actual Planning SQL; peer receipts in tests are fixtures.',
                    'Actual scientific draft, Research/Knowledge browser inspection and launch remain separate.']}
    (output / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--retry-from', type=Path, help='Retain passing prior cases; retry only missing supervision fixtures')
    args = parser.parse_args()
    verify(args.installation.absolute(), args.output.absolute(), None if args.retry_from is None else args.retry_from.absolute())
