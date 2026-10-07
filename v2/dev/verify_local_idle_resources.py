"""Bounded idle owner memory/capacity sample; not a scientific-workload peak benchmark."""

import argparse
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.scientific_workers.engine import ContainerEngine

from local_authoring_controller import AuthoringController
from local_numeric_configuration import write


def verify(configuration, output):
    output.mkdir(parents=True, exist_ok=False)
    write(output / 'owners.json', json.loads((configuration / 'owners.json').read_bytes()))
    thresholds = {'owner_working_set_bytes': 1024**3, 'combined_owner_working_set_bytes': 4 * 1024**3,
                  'control_seconds': .5, 'samples': 5, 'interval_seconds': 1}
    write(output / 'thresholds.json', thresholds)
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    state, vault = LocalState.snapshot(root), (root / 'credentials.dpapi').read_bytes()
    routes = Routes.load(root)
    token = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(['REGISTRY_OPERATOR_TOKEN'])
    controller = AuthoringController(root, output, routes, registry_token=token['REGISTRY_OPERATOR_TOKEN'])
    try:
        controller.start()
        owners = controller.control('/status')['owners']
        pids = {int(row['pid']): name for name, row in owners.items()}
        assert len(pids) == len(owners)
        command = ('Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,'
                   'WorkingSetSize,PrivatePageCount | ConvertTo-Json -Compress')
        samples = []
        for _ in range(thresholds['samples']):
            tick = time.monotonic()
            status = controller.control('/status')
            latency = time.monotonic() - tick
            assert latency < thresholds['control_seconds']
            assert all(row['state'] == 'running' and int(row['pid']) in pids for row in status['owners'].values())
            result = subprocess.run(['powershell', '-NoProfile', '-Command', command], capture_output=True,
                text=True, encoding='utf-8', timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
            assert result.returncode == 0
            rows = json.loads(result.stdout)
            by_pid = {row['ProcessId']: row for row in rows}
            assert set(pids) <= set(by_pid)
            trees, accounted = {}, set()
            for root_pid, name in pids.items():
                included = {root_pid}
                while True:
                    children = {row['ProcessId'] for row in rows if row['ParentProcessId'] in included}
                    expanded = included | children
                    if expanded == included:
                        break
                    included = expanded
                assert not (included & accounted), 'Overlapping owner process trees'
                accounted.update(included)
                tree = [{key: int(by_pid[pid][key]) for key in
                         ('ProcessId', 'ParentProcessId', 'WorkingSetSize', 'PrivatePageCount')}
                        for pid in sorted(included)]
                working_set = sum(row['WorkingSetSize'] for row in tree)
                assert working_set < thresholds['owner_working_set_bytes']
                trees[name] = {'root_pid': root_pid, 'processes': tree, 'working_set_bytes': working_set}
            total = sum(row['working_set_bytes'] for row in trees.values())
            assert total < thresholds['combined_owner_working_set_bytes']
            samples.append({'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'owners': trees, 'combined_working_set_bytes': total, 'control_seconds': latency})
            time.sleep(thresholds['interval_seconds'])
        capacity = ContainerEngine().resources()
        assert capacity['cpus'] >= 2 and capacity['memory'] >= 1024**3
        final = controller.drain()
        assert LocalState.snapshot(root) == state and (root / 'credentials.dpapi').read_bytes() == vault
        write(output / 'evidence.json', {'status': 'passed', 'thresholds': thresholds,
            'samples': samples, 'docker_capacity': capacity, 'final': final, 'provider_calls': 0,
            'limits': ['Five idle API-owner process-tree samples, not full-workload peak RSS/CPU or GPU capacity',
                       'Linux tool profile limits remain2CPU/1GiB/128PIDs; no scientific workers started']})
        print('Idle owner resource/control samples passed within declared bounds; all owners drained', flush=True)
    finally:
        controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configuration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify(args.configuration.absolute(), args.output.absolute())
