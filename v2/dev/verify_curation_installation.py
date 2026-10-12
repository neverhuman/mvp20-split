"""Isolated Planning curation qualification, copied tests and no provider keys."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from sqlalchemy import URL

from install_owner_peer import install
from postgres_fixture import ROOT, owned_state


GROUPS = {
    'contracts_context': ('curation_intake', 'curation_context', 'curation_runtime', 'curation_knowledge',
        'curation_preparation', 'curation_policy', 'curation_input', 'curation_output', 'curation_budget', 'curation_openai'),
    'durable_execution': ('curation_declaration', 'curation_jobs', 'curation_result', 'curation_execution'),
    'compiler_process': ('curation_compiler', 'curation_worker'),
}


def verify(output):
    output.mkdir(parents=True, exist_ok=False)
    python = install(output / 'owner', 'amphora-agent-planning',
        ['amphora_campaign_runtime', 'amphora_data_artifacts', 'amphora_research', 'amphora_knowledge',
         'amphora_capability_registry', 'amphora_deployment', 'amphora_local_gateway'])
    copied = output / 'root'
    tests = copied / 'services/agent_planning/tests'
    shutil.copytree(ROOT / 'services/agent_planning/tests', tests,
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for relative in ('contracts/planning/tests/campaign_output/fixtures', 'contracts/supervision/tests/fixtures'):
        shutil.copytree(ROOT / relative, copied / relative)
    state = owned_state()
    host, port = state['endpoint'].split(':')
    url = URL.create('postgresql+psycopg', username='planning_service', password=state['password'],
        host=host, port=int(port), database=state['database'])
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment.update(PYTHONUTF8='1', PYTHONUNBUFFERED='1', AMPHORA_TEST_POSTGRES='1',
        AMPHORA_TEST_PLANNING_SERVICE_URL=url.render_as_string(hide_password=False),
        AMPHORA_TEST_PLANNING_MIGRATOR_URL=url.set(username='planning_migrator').render_as_string(hide_password=False))

    def run(args, log, timeout=300):
        with log.open('w', encoding='utf-8') as stream:
            result = subprocess.run([str(arg) for arg in args], cwd=output, env=environment,
                stdout=stream, stderr=subprocess.STDOUT, timeout=timeout,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            raise RuntimeError('Independent curation verification failed; inspect ' + log.name)

    run([ROOT / '.venv/Scripts/uv.exe', 'pip', 'install', '--python', python,
         'pytest>=8,<9', 'jsonschema>=4,<5', 'httpx>=0.28,<1'], output / 'test-install.log')
    counts = {}
    for name, areas in GROUPS.items():
        print('Verifying isolated curation group: ' + name, flush=True)
        xml = output / (name + '.xml')
        arguments = [*(str(tests / area) for area in areas), '--confcutdir=' + str(tests),
            '--import-mode=importlib', '-o', 'markers=postgres: explicit database fixture',
            '-v', '--tb=short', '--junitxml=' + str(xml)]
        run([python, '-I', '-c', 'import pytest; raise SystemExit(pytest.main(' + repr(arguments) + '))'],
            output / (name + '.log'), timeout=1200)
        suites = ET.parse(xml).getroot().findall('testsuite')
        assert suites and all(int(s.attrib[key]) == 0 for s in suites for key in ('errors', 'failures', 'skipped'))
        counts[name] = sum(int(s.attrib['tests']) for s in suites)
        print(name + ': ' + str(counts[name]) + ' passed', flush=True)
    record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
        'tests': counts, 'external_provider_calls': 0,
        'installation': json.loads((output / 'owner/manifest.json').read_bytes()),
        'limits': ['Actual isolated Planning wheel with public dependency closure; copied test support only',
            'Actual owned PostgreSQL fixture and new scoped requests; unchanged migration0025 replayed',
            'Scripted public owner/provider peers; actual configured CLI process death/replacement',
            'Environment excludes provider keys; no model network or scientific-validity claim',
            'Serving local/LAN demo installations unchanged; integrated actual-owner qualification remains P5']}
    (output / 'evidence.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'tests': sum(counts.values()), 'external_provider_calls': 0}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    verify(parser.parse_args().output.absolute())
