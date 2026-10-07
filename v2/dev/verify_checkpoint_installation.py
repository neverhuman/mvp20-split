"""Independent Planning wheel and copied checkpoint tests; no provider credentials/calls."""

import argparse
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from sqlalchemy import URL

from install_owner_peer import install
from postgres_fixture import ROOT, owned_state


def verify(output):
    output.mkdir(parents=True, exist_ok=False)
    python = install(output / 'owner', 'amphora-agent-planning',
        ['amphora_campaign_runtime', 'amphora_data_artifacts', 'amphora_research', 'amphora_knowledge'])
    copied = output / 'root'
    tests = copied / 'services/agent_planning/tests'
    shutil.copytree(ROOT / 'services/agent_planning/tests', tests,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(ROOT / 'contracts/supervision/tests/fixtures', copied / 'contracts/supervision/tests/fixtures')
    state = owned_state()
    host, port = state['endpoint'].split(':')
    url = URL.create('postgresql+psycopg', username='planning_service', password=state['password'],
                     host=host, port=int(port), database=state['database'])
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment.update(PYTHONUTF8='1', AMPHORA_TEST_POSTGRES='1',
        AMPHORA_TEST_PLANNING_SERVICE_URL=url.render_as_string(hide_password=False),
        AMPHORA_TEST_PLANNING_MIGRATOR_URL=url.set(username='planning_migrator').render_as_string(hide_password=False))

    def run(args):
        result = subprocess.run([str(arg) for arg in args], cwd=output, env=environment,
            capture_output=True, text=True, encoding='utf-8', timeout=240,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        with (output / 'verification.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError('Independent checkpoint verification failed; inspect local verification.log')

    run([ROOT / '.venv/Scripts/uv.exe', 'pip', 'install', '--python', python, 'pytest>=8,<9', 'jsonschema>=4,<5'])
    xml = output / 'tests.xml'
    areas = ('checkpoint_input', 'campaign_packet_profiles', 'campaign_packet', 'campaign_preparations',
             'checkpoint_openai', 'checkpoint_budget')
    arguments = [*(str(tests / area) for area in areas), '--confcutdir=' + str(tests),
        '--import-mode=importlib', '-o', 'markers=postgres: explicit database fixture',
        '-q', '--tb=short', '--junitxml=' + str(xml)]
    run([python, '-I', '-c', 'import pytest; raise SystemExit(pytest.main(' + repr(arguments) + '))'])
    suites = ET.parse(xml).getroot().findall('testsuite')
    assert suites and all(int(s.attrib[key]) == 0 for s in suites for key in ('errors', 'failures', 'skipped'))
    record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
        'tests': sum(int(s.attrib['tests']) for s in suites),
        'installation': json.loads((output / 'owner/manifest.json').read_bytes()),
        'limits': ['Actual isolated Planning wheel and public dependency closure; copied test support only',
            'Actual existing dev PostgreSQL fixture; unchanged schema0020 repeat migration, new scoped test records',
            'Scripted Data and intercepted model transport; no live API calls or provider credentials',
            'No local-demo serving owner replacement or scientific eligibility claim']}
    (output / 'evidence.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': record['status'], 'tests': record['tests'], 'external_provider_calls': 0}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    verify(parser.parse_args().output.absolute())
