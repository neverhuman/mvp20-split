"""Drain original completed-campaign reservations through the bounded native worker."""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from local_demo_controller import Controller
from local_numeric_configuration import write


def verify(campaign_directory, output):
    output.mkdir(parents=True, exist_ok=False)
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    state, routes = LocalState.snapshot(root), Routes.load(root)
    tokens = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment([
        'RUNTIME_OPERATOR_TOKEN', 'REGISTRY_OPERATOR_TOKEN', 'RUNTIME_ARTIFACT_TOKEN'])
    original = json.loads((campaign_directory / 'retention-diagnostic.json').read_bytes())
    admission = json.loads((campaign_directory / 'admission.json').read_bytes())
    controller = Controller(root, campaign_directory, routes, 'admitted')
    try:
        controller.start_owners(tokens['REGISTRY_OPERATOR_TOKEN'])
        def read(owner, path, reference):
            code, record = controller.request(routes.endpoint(owner), path, token=tokens[reference])
            assert code == 200
            return record
        before = read('runtime', '/v3/graph-runs/' + admission['run_id'], 'RUNTIME_OPERATOR_TOKEN')
        assert before['status'] == 'completed' and before['spent'] == 15
        controller.control('/workers/runtime-deliver/start', 'POST')
        retained = {}
        started = time.monotonic()
        last = None
        def confirmed():
            nonlocal last
            for key in original['retained']:
                retained[key] = read('artifact', '/v1/reservations/' + key, 'RUNTIME_ARTIFACT_TOKEN')
            count = sum(record['outcome']['status'] == 'confirmed' for record in retained.values())
            if count != last:
                print(json.dumps({'confirmed_original_outputs': count, 'total': len(retained)}), flush=True)
                write(output / 'progress.json', retained)
                last = count
            return count == len(retained)
        controller.wait(confirmed, timeout=120)
        elapsed = time.monotonic() - started
        assert len(retained) == 15
        after = read('runtime', '/v3/graph-runs/' + admission['run_id'], 'RUNTIME_OPERATOR_TOKEN')
        assert before == after
        worker = controller.control('/status')['workers']['runtime-deliver']
        final = controller.drain()
    finally:
        controller.close()
    write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'passed', 'run_id': admission['run_id'], 'before': before, 'after': after,
        'retained': retained, 'delivery_worker': worker, 'final': final, 'seconds': elapsed,
        'limit_seconds': 120, 'scientific_reruns': 0, 'provider_calls': 0,
        'limits': ['Original completed graph/receipts unchanged; no science rerun or synthetic acknowledgement',
            'Unconfigured notifications remain unavailable; only real Artifact confirmations establish this recovery',
            'Existing backlog recovery; a fresh full campaign still must pass the original gate']})
    print('All15 original output reservations confirmed without rerunning science', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign-directory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify(args.campaign_directory.absolute(), args.output.absolute())
