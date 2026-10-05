"""Independent Runtime scope policy and unchanged predecessor payload proof; no SQL."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_tool_images import closure
from check_boundaries import ROOT, project_specs


def verify(output, predecessor):
    output, predecessor = output.absolute(), predecessor.absolute()
    output.mkdir(parents=True, exist_ok=False)
    wheels = output / 'wheels'
    wheels.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith('AMPHORA') and key != 'PYTHONPATH'}
    env['PYTHONUTF8'] = '1'
    specs = {cfg['project']['name']: (path, cfg, module) for path, cfg, module in project_specs()}
    uv = ROOT / '.venv/Scripts/uv.exe'

    def run(args):
        result = subprocess.run([str(arg) for arg in args], cwd=output, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', timeout=120)
        with (output / 'verification.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout)
        assert result.returncode == 0, 'Independent Runtime scope check failed; inspect verification.log'

    for name in sorted(closure('amphora-campaign-runtime', specs)):
        run([uv, 'build', '--project', specs[name][0], '--wheel', '--out-dir', wheels])
    environment = output / 'environment'
    run([uv, 'venv', '--python', sys.executable, environment])
    python = environment / 'Scripts/python.exe'
    run([uv, 'pip', 'install', '--python', python, *sorted(wheels.glob('*.whl')), 'pytest>=8,<9'])
    run([python, '-I', '-c', "import importlib.util,sys; from pathlib import Path; import amphora_campaign_runtime; "
         "assert Path(amphora_campaign_runtime.__file__).absolute().is_relative_to(Path(sys.prefix).absolute()); "
         "assert all(importlib.util.find_spec(n) is None for n in "
         "('amphora_agent_planning','amphora_research','amphora_knowledge','amphora_data_artifacts','amphora_capability_registry'))"])
    old_root = predecessor / 'Lib/site-packages/amphora_campaign_runtime'
    assert old_root.is_dir(), 'Explicit prior installed Runtime required'
    prior = {str(path.relative_to(old_root)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in old_root.rglob('*') if path.suffix in {'.py', '.sql', '.json'} and '__pycache__' not in path.parts}
    wheel = next(wheels.glob('amphora_campaign_runtime-*.whl'))
    with zipfile.ZipFile(wheel) as archive:
        for name, sha in prior.items():
            assert hashlib.sha256(archive.read('amphora_campaign_runtime/' + name)).hexdigest() == sha, name
    assert prior
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc')
    shutil.copytree(ROOT / 'services/campaign_runtime/tests/supervision_scope', output / 'tests/scope', ignore=ignore)
    shutil.copytree(ROOT / 'contracts/graph_runtime/tests', output / 'tests/contracts/tests', ignore=ignore)
    shutil.copytree(ROOT / 'contracts/graph_runtime/examples', output / 'tests/contracts/examples', ignore=ignore)
    suites = []
    for index, area in enumerate(('scope', 'contracts/tests')):
        report = output / f'tests-{index}.xml'
        run([python, '-I', '-m', 'pytest', output / 'tests' / area, '--import-mode=importlib', '-q',
             '--tb=short', '--junitxml=' + str(report)])
        suites.extend(ET.parse(report).getroot().findall('testsuite'))
    tests = sum(int(s.attrib['tests']) for s in suites)
    assert tests and all(int(s.attrib[key]) == 0 for s in suites for key in ('errors', 'failures', 'skipped'))
    manifest = {'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'runtime': specs['amphora-campaign-runtime'][1]['project']['version'],
        'tests': tests, 'seconds': sum(float(s.attrib['time']) for s in suites),
        'unchanged_predecessor_payload': prior, 'predecessor_installation': str(predecessor),
        'wheels': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(wheels.glob('*.whl'))},
        'limits': ['Pure scope policy and public contract compatibility; no SQL or peer hosts',
                   'Prior Runtime production Python/SQL/JSON bytes unchanged; new module grants no acceptance authority']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'tests': tests, 'unchanged_predecessor_files': len(prior)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--predecessor', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.predecessor)
