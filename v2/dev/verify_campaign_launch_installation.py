"""Independent launch installation plus actual process/container recovery fixtures."""
import argparse
import json
import os
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from check_boundaries import ROOT
from install_owner_peer import install


def verify(output, bundle=None, registry_python=None, *, launch_only=False):
    output.mkdir(parents=True, exist_ok=False)
    if not launch_only:
        if bundle is None or registry_python is None:
            raise ValueError('Full qualification requires bundle and Registry interpreter')
        bundle.mkdir(parents=True, exist_ok=False)
    python = install(output / 'owner', 'amphora-deployment', [
        'amphora_campaign_runtime', 'amphora_agent_planning', 'amphora_data_artifacts',
        'amphora_capability_registry', 'amphora_knowledge_graph', 'sqlalchemy'])
    tests = output / 'tests'
    shutil.copytree(ROOT / 'deploy/local/tests', tests, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('verify_campaign_launch_recovery.py', 'verify_scientific_monitor_recovery.py'):
        shutil.copyfile(ROOT / 'dev' / name, output / name)
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment.update(PYTHONUTF8='1')
    if registry_python is not None:
        environment['AMPHORA_TEST_REGISTRY_PYTHON'] = str(registry_python)
    def run(arguments):
        result = subprocess.run([str(arg) for arg in arguments], cwd=output, env=environment,
            capture_output=True, text=True, encoding='utf-8', timeout=240, check=False,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        with (output / 'verification.log').open('a', encoding='utf-8') as stream:
            stream.write(result.stdout + result.stderr)
        assert result.returncode == 0, 'Launch qualification failed; inspect local verification.log'
    run([ROOT / '.venv/Scripts/uv.exe', 'pip', 'install', '--python', python, 'pytest>=8,<9'])
    xml = output / 'tests.xml'
    arguments = [str(tests / 'campaign_launch' if launch_only else tests), '--confcutdir=' + str(tests), '--import-mode=importlib', '-q', '--tb=short', '--junitxml=' + str(xml)]
    run([python, '-I', '-c', 'import pytest; raise SystemExit(pytest.main(' + repr(arguments) + '))'])
    suites = ET.parse(xml).getroot().findall('testsuite')
    assert suites and all(int(s.attrib[key]) == 0 for s in suites for key in ('errors', 'failures', 'skipped'))
    if launch_only:
        evidence = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status':'passed',
            'tests':sum(int(s.attrib['tests']) for s in suites),
            'installation':json.loads((output / 'owner/manifest.json').read_bytes()),
            'limits':['Fresh owner/public-contract wheels; scoped fresh/successor lifecycle tests',
                'Actual private SQLite and local HTTP; scripted Runtime/worker peers; no live demo or paid model calls',
                'No container recovery probe or actual Runtime admission claimed by this bounded mode']}
        (output / 'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':'passed','tests':evidence['tests'],'scope':'launch-only'}),flush=True)
        return
    run([python, '-I', output / 'verify_campaign_launch_recovery.py', 'verify', '--output', output / 'receipt-recovery'])
    # Fresh fixture TLS credentials stay in the private physical bundle. No active
    # demo endpoints, certificates, daemon restart or provider credentials are used.
    run([python, '-I', '-c', 'from amphora_deployment.tool_access import TLSIdentity; '
        + 'TLSIdentity.create(' + repr(str(bundle / 'tls')) + ',' + repr(uuid.uuid4().hex)
        + ',"C:/Program Files/Git/usr/bin/openssl.exe")'])
    for phase in ('started', 'intent', 'created'):
        args = [python, '-I', output / 'verify_scientific_monitor_recovery.py', 'verify',
            '--output', output / ('container-' + phase), '--bundle-directory', bundle / phase,
            '--identity-directory', bundle / 'tls']
        if phase != 'started': args += ['--prepared-phase', phase]
        run(args)
    evidence = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
        'tests': sum(int(s.attrib['tests']) for s in suites),
        'installation': json.loads((output / 'owner/manifest.json').read_bytes()),
        'receipt_recovery': json.loads((output / 'receipt-recovery/evidence.json').read_bytes()),
        'container_recovery': {phase: json.loads((output / ('container-' + phase) / 'evidence.json').read_bytes())
            for phase in ('started', 'intent', 'created')},
        'limits': ['Receipt authority is an HTTP fixture; actual campaign admission and browser Run remain L4',
            'Actual isolated process death/container adoption; no active-demo outage or paid model calls']}
    (output / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'passed', 'tests': evidence['tests'], 'recovery_probes': 4}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bundle-directory', type=Path)
    parser.add_argument('--registry-python', type=Path)
    parser.add_argument('--launch-only', action='store_true')
    args = parser.parse_args()
    verify(args.output.absolute(), args.bundle_directory.absolute() if args.bundle_directory else None,
           args.registry_python.absolute() if args.registry_python else None, launch_only=args.launch_only)
