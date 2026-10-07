"""Local Studio/gateway inspection and optional draft validation; no SQL, workers or model calls."""

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState

from check_boundaries import ROOT
from local_authoring_controller import AuthoringController
from local_numeric_configuration import write


class BrowserController(AuthoringController):
    def start(self):
        super().start()
        self.control('/owners/gateway/start', 'POST')
        def ready():
            with self.opener.open(self.routes.endpoint('gateway') + '/', timeout=3) as response:
                return response.status == 200
        self.wait(ready)

    def drain(self):
        self.control('/owners/gateway/drain', 'POST')
        self.wait(lambda: self.control('/status')['owners']['gateway']['state'] == 'exited')
        return super().drain()


def verify(configuration, retained, public, output):
    output.mkdir(parents=True, exist_ok=False)
    prepared = json.loads((configuration / 'prepared.json').read_bytes())
    original = json.loads((retained / 'evidence.json').read_bytes())
    assert original['status'] == 'passed'
    owners = json.loads((configuration / 'owners.json').read_bytes())['owners']
    authoring = (configuration / 'authoring-evidence.json').exists()
    owners = {name: value for name, value in owners.items() if authoring or name != 'registry'}
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    state, vault = LocalState.snapshot(root), (root / 'credentials.dpapi').read_bytes()
    routes = Routes.load(root)
    config = {'profile': 'local-gateway-v1', 'public_directory': str(public),
        'peers': {name: {'endpoint': routes.endpoint(name), 'token_env': 'AMPHORA_' + name.upper() + '_OPERATOR_TOKEN'}
                  for name in owners},
        'context': {'actor_id': 'admin', 'scope': prepared['scope'], 'run_id': original['run_id'], 'synthetic': True},
        'launcher_key_env': 'AMPHORA_GATEWAY_SESSION_KEY'}
    gateway_config = write(output / 'gateway.json', config)
    owners['gateway'] = {'installation': str(ROOT.parent / '.test-results/local-gateway-drain-20261006a'),
        'source_lock': str(ROOT / 'services/local_gateway/uv.lock'), 'configuration': str(gateway_config),
        'secret_references': ['GATEWAY_SESSION_KEY'] + [name.upper() + '_OPERATOR_TOKEN' for name in config['peers']]}
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    records = json.loads((configuration / 'owner-readback.json').read_bytes())
    browser_input = write(output / 'browser-input.json', {'origin': routes.endpoint('gateway'),
        'run_id': original['run_id'], 'scope': prepared['scope'], 'objective': prepared['objective'],
        'context': prepared['context'], 'records': records,
        'draft': json.loads((configuration / 'draft.json').read_bytes()) if authoring else None, 'expected_nodes': len(original['result']['graph']['nodes'])})
    tokens = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(['GATEWAY_SESSION_KEY'] + (['REGISTRY_OPERATOR_TOKEN'] if authoring else []))
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment.update(PYTHONUTF8='1', AMPHORA_BROWSER_LAUNCH_KEY=tokens['GATEWAY_SESSION_KEY'])
    controller = BrowserController(root, output, routes, registry_token=tokens.get('REGISTRY_OPERATOR_TOKEN'))
    try:
        controller.start()
        result = subprocess.run(['node', str(ROOT / 'studio/tests/integration/local_demo.mjs'),
            str(browser_input), str(output)], cwd=ROOT / 'studio', env=environment,
            capture_output=True, text=True, encoding='utf-8', timeout=180,
            creationflags=subprocess.CREATE_NO_WINDOW)
        (output / 'browser.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        final = controller.drain()
        assert result.returncode == 0, 'Actual local browser acceptance failed; inspect browser.log'
        assert LocalState.snapshot(root) == state and (root / 'credentials.dpapi').read_bytes() == vault
        write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed', 'run_id': original['run_id'], 'scope': prepared['scope'],
            'browser': json.loads((output / 'browser-evidence.json').read_bytes()), 'final': final,
            'assets': {name: hashlib.sha256((public / name).read_bytes()).hexdigest() for name in ('index.html', 'app.js', 'app.css')},
            'provider_calls': 0, 'workers_started': False,
            'limits': ['Actual localhost gateway/Studio and five retained owners; synthetic science only',
                       'Inspection and optional saved-draft validation; successor admission/trace remains separate']})
        print('Actual local browser execution/reasoning/context inspection passed; zero model calls', flush=True)
    finally:
        controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('configuration', 'retained', 'public', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    verify(*(getattr(args, name).absolute() for name in ('configuration', 'retained', 'public', 'output')))
