"""Fresh Gateway wheel and copied owner tests; no peer implementation or credentials."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

from install_owner_peer import install

ROOT = Path(__file__).absolute().parents[1]


def verify(output):
    output.mkdir(parents=True, exist_ok=False)
    python = install(output / 'owner', 'amphora-local-gateway', ['amphora_agent_planning',
        'amphora_campaign_runtime', 'amphora_deployment', 'amphora_data_artifacts'])
    tests = output / 'tests'
    shutil.copytree(ROOT / 'services/local_gateway/tests', tests,
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment.update(PYTHONUTF8='1', PYTHONUNBUFFERED='1')
    def run(arguments, name):
        with (output / name).open('w', encoding='utf-8') as log:
            result = subprocess.run([str(arg) for arg in arguments], cwd=output, env=environment,
                stdout=log, stderr=subprocess.STDOUT, timeout=300,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            raise RuntimeError('Independent Gateway check failed; inspect ' + name)
    run([ROOT / '.venv/Scripts/uv.exe', 'pip', 'install', '--python', python, 'pytest>=8,<9'], 'test-install.log')
    xml = output / 'gateway.xml'
    arguments = [str(tests), '--confcutdir=' + str(tests), '--import-mode=importlib',
        '-v', '--tb=short', '--junitxml=' + str(xml)]
    run([python, '-I', '-c', 'import pytest; raise SystemExit(pytest.main(' + repr(arguments) + '))'], 'gateway.log')
    suites = ET.parse(xml).getroot().findall('testsuite')
    assert suites and all(int(s.attrib[key]) == 0 for s in suites for key in ('errors', 'failures', 'skipped'))
    count = sum(int(s.attrib['tests']) for s in suites)
    record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed', 'tests': count,
        'installation': json.loads((output / 'owner/manifest.json').read_bytes()),
        'limits': ['Fresh Gateway wheel; copied tests, no peer implementation imports',
            'Scripted public peers and isolated localhost HTTP/TLS; no live-demo change or provider call']}
    (output / 'evidence.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'tests': count}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    verify(parser.parse_args().output.absolute())
