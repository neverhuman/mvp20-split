"""Independent Deployment wheel/tests plus actual installed native worker turns."""

import argparse
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from check_boundaries import ROOT
from install_owner_peer import install


def verify(output, source_manifest, registry_python, planning_installation):
    output.mkdir(parents=True, exist_ok=False)
    python = install(output / 'owner', 'amphora-deployment',
        ['amphora_campaign_runtime', 'amphora_agent_planning', 'amphora_data_artifacts', 'sqlalchemy', 'pydantic'])
    tests = output / 'tests'
    shutil.copytree(ROOT / 'deploy/local/tests', tests, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copyfile(ROOT / 'dev/verify_native_workers.py', output / 'probe.py')
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment.update(PYTHONUTF8='1', AMPHORA_TEST_REGISTRY_PYTHON=str(registry_python))

    def run(arguments):
        result = subprocess.run([str(arg) for arg in arguments], cwd=output, env=environment,
            capture_output=True, text=True, encoding='utf-8', timeout=240, check=False,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        with (output / 'verification.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout + result.stderr)
        assert result.returncode == 0, 'Native qualification failed; inspect local verification.log'

    run([ROOT / '.venv/Scripts/uv.exe', 'pip', 'install', '--python', python, 'pytest>=8,<9'])
    xml = output / 'tests.xml'
    arguments = [str(tests), '--confcutdir=' + str(tests), '--import-mode=importlib', '-q', '--tb=short',
                 '--junitxml=' + str(xml)]
    run([python, '-I', '-c', 'import pytest; raise SystemExit(pytest.main(' + repr(arguments) + '))'])
    suites = ET.parse(xml).getroot().findall('testsuite')
    assert suites and all(int(s.attrib[key]) == 0 for s in suites for key in ('errors', 'failures', 'skipped'))
    run([python, '-I', output / 'probe.py', '--output', output / 'actual', '--source-manifest', source_manifest,
         '--planning-installation', planning_installation,
         '--planning-lock', ROOT / 'services/agent_planning/uv.lock'])
    record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
        'tests': sum(int(s.attrib['tests']) for s in suites),
        'installation': json.loads((output / 'owner/manifest.json').read_bytes()),
        'native_workers': json.loads((output / 'actual/evidence.json').read_bytes())}
    (output / 'evidence.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'tests': record['tests'], 'workers': 2}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-manifest', type=Path, required=True)
    parser.add_argument('--registry-python', type=Path, required=True)
    parser.add_argument('--planning-installation', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output.absolute(), args.source_manifest.absolute(),
           args.registry_python.absolute(), args.planning_installation.absolute())
