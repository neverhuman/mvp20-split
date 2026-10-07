"""Independent Deployment tests and actual scoped Registry peer composition."""

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


def verify(output, source, registry_python):
    output.mkdir(parents=True, exist_ok=False)
    python = install(output / 'owner', 'amphora-deployment',
        ['amphora_campaign_runtime', 'amphora_capability_registry', 'sqlalchemy', 'pydantic'])
    tests = output / 'tests'
    shutil.copytree(ROOT / 'deploy/local/tests', tests, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment.update(PYTHONUTF8='1', AMPHORA_TEST_REGISTRY_PYTHON=str(registry_python))

    def run(arguments, timeout=240):
        result = subprocess.run([str(arg) for arg in arguments], cwd=output, env=environment,
            capture_output=True, text=True, encoding='utf-8', timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW)
        with (output / 'verification.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout + result.stderr)
        assert result.returncode == 0, 'Registry peer qualification failed; inspect verification.log'

    run([ROOT / '.venv/Scripts/uv.exe', 'pip', 'install', '--python', python, 'pytest>=8,<9'])
    xml = output / 'tests.xml'
    args = [str(tests), '--confcutdir=' + str(tests), '--import-mode=importlib', '-q', '--tb=short', '--junitxml=' + str(xml)]
    run([python, '-I', '-c', 'import pytest; raise SystemExit(pytest.main(' + repr(args) + '))'])
    suites = ET.parse(xml).getroot().findall('testsuite')
    assert suites and all(int(s.attrib[key]) == 0 for s in suites for key in ('errors', 'failures', 'skipped'))
    run([python, ROOT / 'dev/verify_local_registry_access.py', '--source', source, '--output', output / 'configuration'], timeout=360)
    write = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
             'tests': sum(int(s.attrib['tests']) for s in suites),
             'installation': json.loads((output / 'owner/manifest.json').read_bytes()),
             'peer': json.loads((output / 'configuration/registry-access-evidence.json').read_bytes())}
    (output / 'evidence.json').write_text(json.dumps(write, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'tests': write['tests'], 'probes': 1}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'source', 'registry-python'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    verify(args.output.absolute(), args.source.absolute(), args.registry_python.absolute())
