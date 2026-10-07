"""Run the public owner-record scenario outside the development interpreter."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from check_boundaries import ROOT
from install_owner_peer import install


def verify(output, source_manifest):
    output.mkdir(parents=True, exist_ok=False)
    python = install(output / 'owner', 'amphora-deployment',
        ['amphora_research', 'amphora_knowledge', 'amphora_data_artifacts', 'sqlalchemy', 'pydantic'])
    scripts = {}
    for name in ('verify_local_owner_records.py', 'local_records_controller.py', 'local_demo_controller.py',
                 'local_numeric_configuration.py'):
        target = output / name
        shutil.copyfile(ROOT / 'dev' / name, target)
        scripts[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    fixture = output / 'initial.json'
    shutil.copyfile(ROOT / 'services/knowledge/tests/fixtures/initial.json', fixture)
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment['PYTHONUTF8'] = '1'
    result = subprocess.run([str(python), str(output / 'verify_local_owner_records.py'),
        '--output', str(output / 'scenario'), '--source-manifest', str(source_manifest), '--fixture', str(fixture)],
        cwd=output, env=environment, capture_output=True, text=True, encoding='utf-8', timeout=360,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    (output / 'verification.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    assert result.returncode == 0, 'Owner record qualification failed; inspect local verification.log'
    record = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'status': 'passed',
        'installation': json.loads((output / 'owner/manifest.json').read_bytes()), 'scripts': scripts,
        'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
        'scenario': json.loads((output / 'scenario/evidence.json').read_bytes())}
    (output / 'evidence.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print('Independent public owner records, restart, scope and immutable declaration checks passed', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-manifest', type=Path, required=True)
    args = parser.parse_args()
    verify(args.output.absolute(), args.source_manifest.absolute())
