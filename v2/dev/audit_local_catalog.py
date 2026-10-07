"""Invoke the independently installed Data owner's public local recovery CLI."""

import argparse
import json
import os
import subprocess
from pathlib import Path

from amphora_deployment.lifecycle.configuration import load_bindings
from amphora_deployment.lifecycle.routes import Routes


def audit(root, manifest, python, output):
    output.mkdir(parents=True, exist_ok=False)
    binding = load_bindings(root, manifest, Routes.load(root))['artifact']
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment.update(binding.environment)
    environment['PYTHONUTF8'] = '1'
    result = subprocess.run([str(python), '-I', '-m', 'amphora_data_artifacts.recovery',
        '--config', str(binding.configuration), '--output', str(output / 'summary.json'),
        '--inventory-output', str(output / 'inventory.jsonl')], env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=330,
        creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode in (0, 3), 'Owner catalog audit incomplete; inspect only retained safe summary'
    summary = json.loads((output / 'summary.json').read_bytes())
    assert (summary['status'] == 'verified') == (result.returncode == 0)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'manifest', 'python', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    audit(*(getattr(args, name).absolute() for name in ('root', 'manifest', 'python', 'output')))
