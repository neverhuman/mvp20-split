"""Independent recovery-owner/tool builds and actual retained history via installed Deployment."""

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


def verify(output, evaluator_baseline, registry_python, root, configuration, retained):
    output.mkdir(parents=True, exist_ok=False)
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment.update(PYTHONUTF8='1', AMPHORA_TEST_REGISTRY_PYTHON=str(registry_python))
    def run(arguments, timeout=300):
        result = subprocess.run([str(arg) for arg in arguments], cwd=output, env=environment,
            capture_output=True, timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
        with (output / 'verification.log').open('ab') as stream:
            stream.write(result.stdout + result.stderr)
        assert result.returncode == 0, 'Recovery independent qualification failed; inspect verification.log'

    records = {}
    for name, package, source, forbidden in (
        ('deployment', 'amphora-deployment', ROOT / 'deploy/local/tests',
         ['amphora_campaign_runtime', 'amphora_data_artifacts', 'amphora_capability_registry', 'sqlalchemy', 'pydantic']),
        ('evaluator', 'amphora-synthetic-objectives-rebuilt', ROOT / 'tools/synthetic_objectives_rebuilt/tests',
         ['amphora_synthetic_objectives', 'amphora_evolution_search', 'amphora_campaign_runtime', 'amphora_data_artifacts', 'sqlalchemy'])):
        directory = output / name
        python = install(directory, package, forbidden)
        tests = directory / 'tests'
        shutil.copytree(source, tests, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        dependencies = ['pytest>=8,<9'] + (['jsonschema>=4,<5'] if name == 'evaluator' else [])
        run([ROOT / '.venv/Scripts/uv.exe', 'pip', 'install', '--python', python, *dependencies])
        xml = directory / 'tests.xml'
        arguments = [str(tests), '--confcutdir=' + str(tests), '--import-mode=importlib',
                     '-q', '--tb=short', '--junitxml=' + str(xml)]
        run([python, '-I', '-c', 'import pytest; raise SystemExit(pytest.main(' + repr(arguments) + '))'])
        suites = ET.parse(xml).getroot().findall('testsuite')
        assert suites and all(int(row.attrib[key]) == 0 for row in suites for key in ('failures', 'errors', 'skipped'))
        manifest = json.loads((directory / 'manifest.json').read_bytes())
        records[name] = {'installation': manifest, 'tests': sum(int(row.attrib['tests']) for row in suites)}
        if name == 'evaluator':
            baseline = json.loads(evaluator_baseline.read_bytes())['installation']
            assert manifest['wheels'] == baseline['wheels'], 'Rebuilt source differs from qualified image closure'
        print(name + ' independent build/copied tests passed', flush=True)
    python = output / 'deployment/environment/Scripts/python.exe'
    script = ROOT / 'dev/inspect_local_integrated.py'
    arguments = [str(script), '--configuration', str(configuration), '--retained', str(retained),
                 '--root', str(root), '--output', str(output / 'actual-readback')]
    launch = ('import pathlib,runpy,sys,amphora_deployment; '
        'assert pathlib.Path(amphora_deployment.__file__).is_relative_to(pathlib.Path(sys.prefix)); '
        'sys.path.insert(0,' + repr(str(ROOT / 'dev')) + '); sys.argv=' + repr(arguments) + '; '
        'runpy.run_path(' + repr(str(script)) + ',run_name="__main__")')
    run([python, '-I', '-c', launch])
    record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
        'owners': records, 'actual_readback': json.loads((output / 'actual-readback/evidence.json').read_bytes()),
        'qualified_evaluator_wheel_closure_unchanged': True, 'provider_calls': 0,
        'limits': ['Same selected Windows host/current user and retained pinned owner images',
                   'Earlier intermittent worker process failures remain unresolved; no operational soak claim']}
    (output / 'evidence.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print('Independent recovery packages and installed Deployment actual history passed', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'evaluator-baseline', 'registry-python', 'root', 'configuration', 'retained'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    verify(*(getattr(args, name).absolute() for name in ('output', 'evaluator_baseline', 'registry_python', 'root', 'configuration', 'retained')))
