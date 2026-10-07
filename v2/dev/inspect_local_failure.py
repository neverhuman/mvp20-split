"""Read retained failed graph/attempt/completion history through actual owner APIs."""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState

from local_authoring_controller import AuthoringController
from local_numeric_configuration import write
from verify_local_successor import Requests


def inspect(configuration, retained, output):
    output.mkdir(parents=True, exist_ok=False)
    admission = json.loads((retained / 'admission.json').read_bytes())
    write(output / 'owners.json', json.loads((configuration / 'owners.json').read_bytes()))
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    state, vault = LocalState.snapshot(root), (root / 'credentials.dpapi').read_bytes()
    routes = Routes.load(root)
    tokens = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(
        ['RUNTIME_OPERATOR_TOKEN', 'REGISTRY_OPERATOR_TOKEN'])
    controller = AuthoringController(root, output, routes, registry_token=tokens['REGISTRY_OPERATOR_TOKEN'])
    try:
        controller.start()
        api = Requests(controller, routes, tokens['RUNTIME_OPERATOR_TOKEN'], admission['scope'], output)
        run = admission['run_id']
        graph = api.read('/v3/graph-runs/' + run)
        page = api.read('/v1/graph-observations/' + run + '/nodes?limit=100')
        assert page['next_cursor'] is None
        token = quote(page['snapshot']['snapshot_token'], safe='')
        details, completions = [], []
        for node in page['nodes']:
            if node['kind'] != 'invoke':
                continue
            detail = api.read('/v1/graph-observations/' + run + '/nodes/' + node['activation_id'] + '?snapshot_token=' + token)
            assert detail['next_cursor'] is None
            details.append(detail)
            for attempt in detail['attempts']:
                if attempt['completion_id']:
                    completions.append(api.read('/v1/runs/' + run + '/completions/' + attempt['completion_id']))
        path = '/v1/graph-runs/supervised' if admission['command']['identity']['command_family'] == 'graph.admit_supervised' else '/v1/graph-runs'
        code, receipt = controller.request(routes.endpoint('runtime'), path, token=tokens['RUNTIME_OPERATOR_TOKEN'], body=admission['command'])
        assert code == 200 and receipt == admission['receipt']
        final = controller.drain()
        assert LocalState.snapshot(root) == state and (root / 'credentials.dpapi').read_bytes() == vault
        write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'readback_passed', 'scope': admission['scope'], 'run_id': run,
            'graph': graph, 'details': details, 'completions': completions, 'receipt': receipt,
            'final': final, 'provider_calls': 0, 'workers_started': False})
        print(json.dumps({'state': graph['status'], 'spent': graph['spent'], 'outcomes':
            [row['result']['outcome'] for row in completions]}), flush=True)
    finally:
        controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('configuration', 'retained', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    inspect(*(getattr(args, name).absolute() for name in ('configuration', 'retained', 'output')))
