"""Current isolated supervisor owners; immutable migrations and public protocol proof."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_tool_images import closure
from campaign_context_fixture.support import environment
from check_boundaries import ROOT, project_specs


def verify(output, runtime_predecessor, planning_predecessor):
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    env = environment()
    specs = {cfg['project']['name']: (path, cfg, module) for path, cfg, module in project_specs()}
    uv = ROOT / '.venv/Scripts/uv.exe'
    owners = {'runtime': ('amphora-campaign-runtime', 'amphora_campaign_runtime', runtime_predecessor.absolute()),
              'planning': ('amphora-agent-planning', 'amphora_agent_planning', planning_predecessor.absolute())}
    wheels = output / 'wheels'
    wheels.mkdir()

    def run(args):
        result = subprocess.run([str(item) for item in args], cwd=output, env=env, capture_output=True,
                                text=True, encoding='utf-8', timeout=180, check=False)
        with (output / 'installation.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout + result.stderr)
        assert result.returncode == 0, 'Installed supervisor verification failed; inspect installation.log'

    needed = set.union(*(closure(owner[0], specs) for owner in owners.values()))
    for name in sorted(needed):
        run([uv, 'build', '--project', specs[name][0], '--wheel', '--out-dir', wheels])
        print(json.dumps({'built': name}), flush=True)
    copied = output / 'root'
    for rel in ('services/campaign_runtime/tests', 'services/agent_planning/tests', 'contracts/supervision/tests'):
        shutil.copytree(ROOT / rel, copied / rel, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for rel in ('contracts/fixtures/v2/executable_cases.json',):
        (copied / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, copied / rel)
    records = {}
    private = {'amphora_campaign_runtime', 'amphora_agent_planning', 'amphora_data_artifacts',
               'amphora_knowledge', 'amphora_research', 'amphora_capability_registry'}
    for owner, (package, module, predecessor) in owners.items():
        required = sorted(closure(package, specs))
        archives = [next(wheels.glob(name.replace('-', '_') + '-*.whl')) for name in required]
        source = predecessor / 'Lib/site-packages' / module / 'persistence/migrations/versions'
        assert source.is_dir(), 'Explicit prior installed migration history required'
        prior = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir() if p.suffix in {'.py', '.sql'}}
        assert prior
        with zipfile.ZipFile(next(wheels.glob(package.replace('-', '_') + '-*.whl'))) as archive:
            for name, digest in prior.items():
                assert hashlib.sha256(archive.read(module + '/persistence/migrations/versions/' + name)).hexdigest() == digest, name
        item = {'version': specs[package][1]['project']['version'], 'unchanged_migrations': prior, 'installations': []}
        for label in ('initial', 'replacement'):
            installation = output / owner / label
            run([uv, 'venv', '--python', sys.executable, installation])
            python = installation / 'Scripts/python.exe'
            run([uv, 'pip', 'install', '--python', python, *archives, 'pytest>=8,<9', 'httpx>=0.28,<1'])
            excluded = tuple(sorted(private - {module}))
            run([python, '-I', '-c', 'import importlib.util,sys; from pathlib import Path; '
                f'import {module}; assert Path({module}.__file__).absolute().is_relative_to(Path(sys.prefix).absolute()); '
                f'assert all(importlib.util.find_spec(name) is None for name in {excluded!r})'])
            areas = [('contracts/supervision/tests', None)]
            if owner == 'runtime':
                areas.extend(('services/campaign_runtime/tests/' + area, None)
                             for area in ('supervision_client', 'supervision_responses', 'supervision_capture'))
                areas.append(('services/campaign_runtime/tests/supervision_journal', ['test_frames.py', 'test_series.py']))
            else:
                areas.extend([('services/agent_planning/tests/supervision_client', None),
                              ('services/agent_planning/tests/supervision_api', ['test_credentials.py', 'test_bounds.py'])])
            suites = []
            for index, (relative, files) in enumerate(areas):
                area = copied / relative
                report = output / f'{owner}-{label}-{index}.xml'
                tests = [area] if files is None else [area / file for file in files]
                run([python, '-I', '-m', 'pytest', *tests, '--confcutdir=' + str(area), '--import-mode=importlib',
                     '-q', '--tb=short', '--junitxml=' + str(report)])
                suites.extend(ET.parse(report).getroot().findall('testsuite'))
            assert all(int(s.attrib[key]) == 0 for s in suites for key in ('errors', 'failures', 'skipped'))
            tests = sum(int(s.attrib['tests']) for s in suites)
            item['installations'].append({'label': label, 'tests': tests, 'python': str(python),
                                          'seconds': sum(float(s.attrib['time']) for s in suites)})
            print(json.dumps({'owner': owner, 'installation': label, 'tests': tests}), flush=True)
        records[owner] = item
    schemas = ROOT / 'contracts/schemas'
    schema_pins = {p.relative_to(schemas).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in schemas.rglob('*.json') if p.name != 'manifest.json'}
    assert len(schema_pins) == 528
    previous = json.loads((ROOT / 'contracts/supervision/tests/fixtures/request_predecessor_schema_pins.json').read_bytes())['schemas']
    assert all(schema_pins[name] == digest for name, digest in previous.items())
    manifest = {'status': 'passed', 'verified_at': datetime.now(ZoneInfo('America/Chicago')).strftime('%Y-%m-%d %H:%M:%S'),
                'owners': records, 'schema_pins': schema_pins, 'unchanged_predecessor_schemas': len(previous),
                'wheels': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in wheels.glob('*.whl')},
                'limits': ['No SQL migration/reset or actual owner host in this installation gate',
                           'Peer-private packages absent; copied tests only, production runs from wheels',
                           'Current service HTTP files intentionally changed; only historical migrations asserted byte-identical']}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runtime-predecessor', type=Path, required=True)
    parser.add_argument('--planning-predecessor', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output, args.runtime_predecessor, args.planning_predecessor)
