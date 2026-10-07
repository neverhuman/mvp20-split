"""Fresh Deployment wheel, copied tests and actual Linux SDK transport proof."""

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


def verify(output, identity_directory, registry_python):
    assert registry_python.is_file(), 'Separately installed Registry interpreter required'
    output.mkdir(parents=True, exist_ok=False)
    python = install(output / 'owner', 'amphora-deployment',
        ['amphora_campaign_runtime', 'amphora_agent_planning', 'amphora_data_artifacts', 'sqlalchemy', 'pydantic'])
    tests = output / 'tests'
    shutil.copytree(ROOT / 'deploy/local/tests', tests, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copyfile(ROOT / 'dev/verify_tool_tls.py', output / 'container_probe.py')
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment['PYTHONUTF8'] = '1'
    environment['AMPHORA_TEST_REGISTRY_PYTHON'] = str(registry_python)

    def run(args):
        result = subprocess.run([str(arg) for arg in args], cwd=output, env=environment,
            capture_output=True, text=True, encoding='utf-8', timeout=180,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        with (output / 'verification.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError('Independent TLS qualification failed; inspect local verification.log')

    run([ROOT / '.venv/Scripts/uv.exe', 'pip', 'install', '--python', python, 'pytest>=8,<9'])
    xml = output / 'tests.xml'
    arguments = [str(tests), '--confcutdir=' + str(tests), '--import-mode=importlib', '-q', '--tb=short',
                 '--junitxml=' + str(xml)]
    run([python, '-I', '-c', 'import pytest; raise SystemExit(pytest.main(' + repr(arguments) + '))'])
    suites = ET.parse(xml).getroot().findall('testsuite')
    assert suites and all(int(s.attrib[key]) == 0 for s in suites for key in ('errors', 'failures', 'skipped'))
    run([python, '-I', output / 'container_probe.py', '--output', output / 'container',
        '--identity-directory', identity_directory, '--image', 'amphora/evolution-search:bp08-0957ff3a65a1',
        '--openssl', 'C:/Program Files/Git/usr/bin/openssl.exe'])
    record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
        'tests': sum(int(s.attrib['tests']) for s in suites),
        'installation': json.loads((output / 'owner/manifest.json').read_bytes()),
        'peer_registry_python': str(registry_python),
        'container': json.loads((output / 'container/evidence.json').read_bytes()),
        'limits': ['Independent Deployment wheel and actual Linux image SDK; synthetic owner HTTP fixture',
                   'No campaign, live scientific tools, database mutation or provider calls',
                   'Managed TLS/worker configuration and actual owner eligibility remain subsequent gates']}
    (output / 'evidence.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'tests': record['tests'], 'container_variants': 3}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--identity-directory', type=Path, required=True)
    parser.add_argument('--registry-python', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output.absolute(), args.identity_directory.absolute(), args.registry_python.absolute())
