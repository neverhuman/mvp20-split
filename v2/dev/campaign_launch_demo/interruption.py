"""Bounded operator drill: stop only the identified supervisor after a real pending turn."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from types import SimpleNamespace

from amphora_deployment.persistence.state import LocalState
from amphora_deployment.scientific_workers.engine import ContainerEngine
from amphora_deployment.scientific_workers.ownership import retained_turns


def verify_process(pid, session):
    assert pid != os.getpid() and pid > 0
    # Numeric PID is the only interpolated PowerShell input; command line contains
    # installed paths, never credentials. Exact manifest bounds the outage scope.
    command = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command',
        f'(Get-CimInstance Win32_Process -Filter "ProcessId = {pid}").CommandLine'],
        capture_output=True, text=True, check=True).stdout.strip()
    prepared = json.loads((session / 'launch-prepared.json').read_bytes())
    assert command.startswith(prepared['deployment_python'])
    assert ' -I -m amphora_deployment.lifecycle serve ' in command
    assert '--manifest ' + str(session / 'owners.json') + ' ' in command


def interrupt(root, session, receipt_path, output, pid):
    session = session.absolute()
    verify_process(pid, session)
    assert not output.exists(), 'Preserve previous interruption evidence'
    identity = LocalState.snapshot(root)['deployment_id']
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_bytes())
            directory = root / 'campaign-launches' / receipt['request_sha256']
            manifest = directory / 'bindings.json'
            if receipt.get('run_id') and manifest.exists():
                bindings = json.loads(manifest.read_bytes())
                assert bindings['run_id'] == receipt['run_id']
                for turn in retained_turns(root, identity):
                    worker = bindings['workers'].get(turn['worker'])
                    if not worker or worker['binding_sha256'] != turn['binding_sha256']:
                        continue
                    if turn['phase'] not in {'created', 'starting', 'started'}:
                        continue
                    observed = ContainerEngine().observe(turn, SimpleNamespace(image_id=worker['image_id']))
                    if observed is None or observed.status not in {'created', 'running'}:
                        continue
                    verify_process(pid, session)  # Recheck immediately before the bounded stop.
                    output.mkdir(parents=True)
                    evidence = {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'interruption_prepared', 'supervisor_pid': pid,
                        'launch': receipt, 'turn': turn, 'container_status': observed.status,
                        'container_id': observed.container_id, 'recovery': 'not_yet_verified'}
                    (output / 'before.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
                    os.kill(pid, signal.SIGTERM)
                    evidence['status'] = 'supervisor_interrupted'
                    (output / 'interrupted.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
                    print('Owned supervisor interrupted after verified pending scientific container', flush=True)
                    return
        time.sleep(.05)
    raise RuntimeError('No eligible pending container observed; no process was stopped')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'session', 'receipt', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--supervisor-pid', type=int, required=True)
    args = parser.parse_args()
    interrupt(args.root, args.session, args.receipt, args.output, args.supervisor_pid)
