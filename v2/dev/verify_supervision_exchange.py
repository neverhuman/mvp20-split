"""Two isolated Runtime installations, supervisor compatibility and checkout-byte proof."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from verify_runtime_scope import ROOT
from verify_runtime_scope import verify as verify_scope


def checkout_proof(safe_directory):
    fixtures = ROOT / 'contracts/supervision/tests/fixtures'
    expected = {f'{label}-command.json': sha for label, sha in
                json.loads((fixtures / 'command-pins.json').read_bytes()).items()}
    for label in ('abstain', 'evidence', 'adjustment'):
        expected[f'capture-{label}.json'] = json.loads((fixtures / f'response-{label}.json').read_bytes())['capture']['sha256']
    expected['planning-request.json'] = json.loads((fixtures / 'request.json').read_bytes())['planning_request_sha256']
    for name, sha in expected.items():
        path = (fixtures / name).relative_to(ROOT.parent).as_posix()
        raw = subprocess.check_output(['git', '-c', 'safe.directory=' + safe_directory, '-c', 'core.autocrlf=true',
            'cat-file', '--filters', '--path=' + path, 'HEAD:' + path], cwd=ROOT.parent, timeout=30)
        assert hashlib.sha256(raw).hexdigest() == sha, 'Checkout changes exact fixture bytes: ' + name
        assert hashlib.sha256((fixtures / name).read_bytes()).hexdigest() == sha, name
    pins = json.loads((fixtures / 'request_predecessor_schema_pins.json').read_bytes())['schemas']
    for name, sha in pins.items():
        assert hashlib.sha256((ROOT / 'contracts/schemas' / name).read_bytes()).hexdigest() == sha, name
    return {'autocrlf': True, 'fixtures': expected, 'unchanged_predecessor_schemas': len(pins)}


def verify(output, predecessor, safe_directory):
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    checkout = checkout_proof(safe_directory)
    initial = output / 'initial'
    verify_scope(initial, predecessor)
    initial_manifest = json.loads((initial / 'manifest.json').read_bytes())
    root = output / 'root'
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc')
    for relative in ('services/campaign_runtime/tests/supervision_requests',
                     'services/campaign_runtime/tests/supervision_responses',
                     'contracts/supervision/tests', 'contracts/commands/tests'):
        shutil.copytree(ROOT / relative, root / relative, ignore=ignore)
    env = {key: value for key, value in os.environ.items() if not key.startswith('AMPHORA') and key != 'PYTHONPATH'}
    env['PYTHONUTF8'] = '1'

    def run(args):
        result = subprocess.run([str(arg) for arg in args], cwd=root, env=env, capture_output=True,
            text=True, encoding='utf-8', timeout=120)
        with (output / 'exchange.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout + result.stderr)
        assert result.returncode == 0, 'Independent exchange check failed; inspect exchange.log'

    def suites(python, label, areas):
        observed = []
        for index, area in enumerate(areas):
            report = output / f'{label}-{index}.xml'
            run([python, '-I', '-m', 'pytest', root / area, '--import-mode=importlib', '-q', '--tb=short',
                 '--junitxml=' + str(report)])
            observed.extend(ET.parse(report).getroot().findall('testsuite'))
            print(json.dumps({'installation': label, 'verified_area': area}), flush=True)
        tests = sum(int(s.attrib['tests']) for s in observed)
        assert tests and all(int(s.attrib[key]) == 0 for s in observed for key in ('failures', 'errors', 'skipped'))
        return {'tests': tests, 'seconds': sum(float(s.attrib['time']) for s in observed), 'areas': areas}

    areas = ['services/campaign_runtime/tests/supervision_requests',
             'services/campaign_runtime/tests/supervision_responses',
             'contracts/supervision/tests', 'contracts/commands/tests']
    fresh = suites(initial / 'environment/Scripts/python.exe', 'initial', areas)
    replacement = output / 'replacement'
    uv = ROOT / '.venv/Scripts/uv.exe'
    run([uv, 'venv', '--python', sys.executable, replacement])
    python = replacement / 'Scripts/python.exe'
    run([uv, 'pip', 'install', '--python', python, *sorted((initial / 'wheels').glob('*.whl')), 'pytest>=8,<9'])
    run([python, '-I', '-c', "import importlib.util,sys; from pathlib import Path; import amphora_campaign_runtime; "
         "assert Path(amphora_campaign_runtime.__file__).absolute().is_relative_to(Path(sys.prefix).absolute()); "
         "assert all(importlib.util.find_spec(n) is None for n in "
         "('amphora_agent_planning','amphora_research','amphora_knowledge','amphora_data_artifacts','amphora_capability_registry'))"])
    replay = suites(python, 'replacement', areas[:3])
    manifest = {'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'runtime': initial_manifest['runtime'], 'installations': 2,
        'scope_and_predecessor': initial_manifest, 'initial_exchange': fresh, 'replacement_exchange': replay,
        'checkout_bytes': checkout,
        'limits': ['Independent installation and retained literal profile replay, not independently authored replacement',
                   'No SQL/migrations, HTTP owners, execution decision, provider call or scientific claim']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'initial_tests': initial_manifest['tests'] + fresh['tests'],
                      'replacement_tests': replay['tests']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--predecessor', type=Path, required=True)
    parser.add_argument('--git-safe-directory', default=ROOT.parent.as_posix())
    args = parser.parse_args()
    verify(args.output, args.predecessor, args.git_safe_directory)
