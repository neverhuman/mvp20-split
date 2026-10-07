"""Build isolated Deployment, run copied owned tests and verify the frozen ledger."""

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


def verify(output, registry_python, ledger):
    python = install(output, 'amphora-deployment', [
        'amphora_campaign_runtime', 'amphora_data_artifacts',
        'amphora_capability_registry', 'sqlalchemy', 'pydantic'])
    tests = output / 'tests'
    shutil.copytree(ROOT / 'deploy/local/tests', tests,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment.update(PYTHONUTF8='1', AMPHORA_TEST_REGISTRY_PYTHON=str(registry_python))

    def run(arguments):
        result = subprocess.run([str(arg) for arg in arguments], env=environment,
            cwd=output, capture_output=True, timeout=300, creationflags=subprocess.CREATE_NO_WINDOW)
        with (output / 'acceptance.log').open('ab') as stream:
            stream.write(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError('independent_acceptance_failed')
        return result.stdout

    run([ROOT / '.venv/Scripts/uv.exe', 'pip', 'install', '--python', python, 'pytest>=8,<9'])
    xml = output / 'tests.xml'
    arguments = [str(tests), '--confcutdir=' + str(tests), '--import-mode=importlib',
                 '-q', '--tb=short', '--junitxml=' + str(xml)]
    run([python, '-I', '-c', 'import pytest; raise SystemExit(pytest.main(' + repr(arguments) + '))'])
    suites = ET.parse(xml).getroot().findall('testsuite')
    if not suites or any(int(suite.attrib[key]) for suite in suites for key in ('failures', 'errors', 'skipped')):
        raise RuntimeError('independent_test_outcome_rejected')
    report = json.loads(run([python, '-I', '-m', 'amphora_deployment.acceptance',
        '--ledger', ledger, '--evidence-directory', ledger.parent]))
    if report['status'] != 'verified':
        raise RuntimeError('independent_ledger_rejected')
    record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
              'status': 'passed', 'installation': json.loads((output / 'manifest.json').read_bytes()),
              'tests': sum(int(suite.attrib['tests']) for suite in suites), 'ledger': report,
              'provider_calls': 0, 'limits': ['Copied owned tests and frozen evidence; actual owner/browser smoke is separate']}
    (output / 'evidence.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'tests': record['tests']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'registry-python', 'ledger'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        verify(args.output.absolute(), args.registry_python.absolute(), args.ledger.absolute())
    except Exception:
        raise SystemExit('Independent acceptance failed; retain scoped output.') from None
