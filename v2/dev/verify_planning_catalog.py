"""Run scoped catalog-scale probes against a verified unchanged Planning wheel."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tomllib
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).absolute().parents[1]


def verify(installation, output):
    installation, output = installation.absolute(), output.absolute()
    current = tomllib.loads((ROOT / 'services/agent_planning/pyproject.toml').read_text())['project']['version']
    proof = json.loads((installation / 'manifest.json').read_bytes())
    assert proof['status'] == 'passed' and proof['planning'] == current and proof['scope'] == 'semantic'
    output.mkdir(parents=True, exist_ok=False)
    tests = output / 'tests/service'
    shutil.copytree(installation / 'tests/service', tests)
    source = ROOT / 'services/agent_planning/tests/campaign_catalog'
    shutil.copytree(source, tests / 'campaign_catalog', dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source.glob('*.py')}
    python = installation / 'environment/Scripts/python.exe'
    env = {key: value for key, value in os.environ.items() if not key.startswith('AMPHORA') and key != 'PYTHONPATH'}
    env['PYTHONUTF8'] = '1'
    subprocess.run([str(python), '-I', '-c',
        f"from importlib.metadata import version; assert version('amphora-agent-planning') == {current!r}"],
        cwd=output, env=env, check=True, timeout=20, capture_output=True)
    report = output / 'tests.xml'
    result = subprocess.run([str(python), '-I', '-m', 'pytest', str(tests / 'campaign_catalog'),
        '--import-mode=importlib', '--tb=short', '-q', '-o', 'junit_family=xunit1', '--junitxml=' + str(report)],
        cwd=output, env=env, capture_output=True, text=True, encoding='utf-8', timeout=120)
    (output / 'tests.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    assert result.returncode == 0, 'Catalog acceptance failed; inspect retained tests.log'
    suites = ET.parse(report).getroot().findall('testsuite')
    assert suites and all(int(s.attrib[key]) == 0 for s in suites for key in ('errors', 'failures', 'skipped'))
    count = sum(int(s.attrib['tests']) for s in suites)
    metrics = {case.attrib['name']: {p.attrib['name']: p.attrib['value'] for p in case.iter('property')}
               for suite in suites for case in suite.iter('testcase')}
    manifest = {'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'planning': current, 'tests': count, 'seconds': sum(float(s.attrib['time']) for s in suites),
        'metrics': metrics, 'test_sha256': hashes, 'installation_manifest': str(installation / 'manifest.json'),
        'limits': ['Verified unchanged implementation with current hash-recorded test overlay',
            'Actual bounded client against a protocol catalog stub; no actual Registry deployment or natural-language quality claim']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'tests': count, 'metrics': metrics}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify(args.installation, args.output)
