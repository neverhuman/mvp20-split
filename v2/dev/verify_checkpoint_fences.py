"""Run actual SQL checkpoint freshness/fences from two isolated current Runtime wheels."""

import argparse
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from campaign_context_fixture.support import environment
from check_boundaries import ROOT


def verify(output, installation):
    assert os.environ.get('AMPHORA_TEST_POSTGRES') == '1'
    output, installation = output.absolute(), installation.absolute()
    proof = json.loads((installation / 'manifest.json').read_bytes())
    assert proof['status'] == 'passed' and proof['owners']['runtime']['version'] == '0.40.0'
    output.mkdir(parents=True, exist_ok=False)
    copied = output / 'root'
    shutil.copytree(installation / 'root', copied, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    relative = Path('services/campaign_runtime/tests/supervision_checkpoints/test_fences.py')
    shutil.copyfile(ROOT / relative, copied / relative)
    env = {**environment(), 'AMPHORA_TEST_POSTGRES': '1'}
    records = []
    for label in ('initial', 'replacement'):
        python = installation / 'runtime' / label / 'Scripts/python.exe'
        report = output / (label + '.xml')
        args = ['-c', str(ROOT / 'dev/pyproject.toml'), str(copied / relative), '-q', '--tb=short', '--junitxml=' + str(report)]
        code = ('import importlib.metadata,importlib.util,sys; from pathlib import Path; import amphora_campaign_runtime; '
            "assert importlib.metadata.version('amphora-campaign-runtime') == '0.40.0'; "
            'assert Path(amphora_campaign_runtime.__file__).absolute().is_relative_to(Path(sys.prefix).absolute()); '
            "assert all(importlib.util.find_spec(n) is None for n in ('amphora_agent_planning','amphora_data_artifacts',"
            "'amphora_research','amphora_knowledge','amphora_capability_registry')); "
            f'import pytest; raise SystemExit(pytest.main({args!r}))')
        result = subprocess.run([str(python), '-I', '-c', code], cwd=output, env=env, capture_output=True,
            text=True, encoding='utf-8', timeout=120, check=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        (output / (label + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        assert result.returncode == 0, 'Installed fence suite failed; inspect installation log'
        suites = ET.parse(report).getroot().findall('testsuite')
        assert all(int(item.attrib[key]) == 0 for item in suites for key in ('failures', 'errors', 'skipped'))
        records.append({'installation': label, 'tests': sum(int(item.attrib['tests']) for item in suites),
                        'seconds': sum(float(item.attrib['time']) for item in suites)})
        print(json.dumps(records[-1]), flush=True)
    manifest = {'status': 'passed', 'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'runtime': '0.40.0', 'migration': 'runtime_0023', 'installations': records,
        'limits': ['Runtime production imports only from isolated wheels; test configuration exposes dev fixture helpers only',
                   'Actual retained PostgreSQL, current migration-to-head is idempotent; no reset or old migrator',
                   'Refresh candidate is explicit validation, not automatic request creation or execution acceptance']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--installation', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.installation)
