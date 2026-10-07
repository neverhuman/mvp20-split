"""Actual scoped Runtime/Registry configuration and least-privilege peer proof."""

import argparse
import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from amphora_deployment.registry_access import provision_registry_credential, registry_credential

from local_authoring_controller import AuthoringController
from local_numeric_configuration import write


def verify(source, output):
    output.mkdir(parents=True, exist_ok=False)
    for path in source.glob('*.json'):
        shutil.copyfile(path, output / path.name)
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    state, original = LocalState.snapshot(root), (root / 'credentials.dpapi').read_bytes()
    provisioned = provision_registry_credential(root)
    assert (root / 'credentials.dpapi').read_bytes() == original
    sidecar = (root / 'runtime-registry.dpapi').read_bytes()
    assert provision_registry_credential(root) == provisioned
    assert (root / 'runtime-registry.dpapi').read_bytes() == sidecar
    routes = Routes.load(root)
    scope = json.loads((source / 'prepared.json').read_bytes())['scope']
    owners = json.loads((source / 'owners.json').read_bytes())['owners']
    runtime = json.loads(Path(owners['runtime']['configuration']).read_bytes())
    registry = json.loads(Path(owners['registry']['configuration']).read_bytes())
    runtime['draft_registry'] = {'endpoint': routes.endpoint('registry'),
        'token_env': 'AMPHORA_RUNTIME_REGISTRY_TOKEN', 'actor_id': 'runtime-draft'}
    registry['principals'].append({'token_env': 'AMPHORA_RUNTIME_REGISTRY_TOKEN', 'actor_id': 'runtime-draft',
        'scope': scope, 'actions': ['read', 'resolve']})
    for owner, configuration in [('runtime', runtime), ('registry', registry)]:
        owners[owner]['configuration'] = str(write(output / (owner + '.json'), configuration))
        owners[owner]['secret_references'] = sorted(set(owners[owner]['secret_references']) | {'RUNTIME_REGISTRY_TOKEN'})
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    operator = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(['REGISTRY_OPERATOR_TOKEN'])
    peer = registry_credential(root, state['deployment_id']).environment(['RUNTIME_REGISTRY_TOKEN'])['RUNTIME_REGISTRY_TOKEN']
    controller = AuthoringController(root, output, routes, registry_token=operator['REGISTRY_OPERATOR_TOKEN'])
    try:
        controller.start()
        def call(path, body=None):
            return controller.request(routes.endpoint('registry'), path, token=peer, body=body)
        code, catalog = call('/v1/releases')
        assert code == 200 and catalog['items']
        assert all(item['scope'] == scope for item in catalog['items'])
        release = runtime['graphs'][0]['releases'][0]
        descriptor = json.loads((output / release['descriptor']).read_bytes())
        identity = {'scope': scope, 'actor_id': 'runtime-draft', 'command_id': uuid.uuid4().hex,
                    'command_family': 'registry.resolve'}
        command = {'identity': identity, 'payload': {'release': release['lock'], 'context': 'synthetic-tests',
                   'inputs': descriptor['tool']['inputs'], 'outputs': descriptor['tool']['outputs']}}
        write(output / 'peer-resolve-command.json', command)
        code, receipt = call('/v1/registry/resolve', command)
        assert code == 200 and receipt['status'] == 'rejected' and receipt['reason_code'] == 'no_eligible_capacity'
        assert call('/v1/registry/resolve', command) == (code, receipt)
        forbidden = {'identity': {**identity, 'command_id': uuid.uuid4().hex, 'command_family': 'registry.activate'},
                     'payload': {'release': release['lock'], 'expected_revision': receipt['release']['revision']}}
        denied_code, denied = call('/v1/registry/activate', forbidden)
        assert denied_code == 403
        final = controller.drain()
        assert LocalState.snapshot(root) == state and (root / 'credentials.dpapi').read_bytes() == original
        assert (root / 'runtime-registry.dpapi').read_bytes() == sidecar
        write(output / 'registry-access-evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed', 'scope': scope, 'provision': provisioned, 'resolve': receipt,
            'forbidden_action': {'status': denied_code, 'result': denied}, 'final': final,
            'provider_calls': 0, 'workers_started': False,
            'limits': ['Actual Registry peer reads/resolution; no live capacity or campaign admission',
                       'Runtime configured with separate peer identity; successor admission remains separate']})
        print('Dedicated Registry peer read/resolve/replay and forbidden-action denial passed', flush=True)
    finally:
        controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify(args.source.absolute(), args.output.absolute())
