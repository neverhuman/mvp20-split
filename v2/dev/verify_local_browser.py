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


def verify(configuration, retained, public, output, successor=None):
    output.mkdir(parents=True, exist_ok=False)
    prepared = json.loads((configuration / 'prepared.json').read_bytes())
    original = json.loads((retained / 'evidence.json').read_bytes())
    assert original['status'] == 'passed'
    selected = json.loads((successor / 'successor-evidence.json').read_bytes()) if successor else None
    if selected:
        assert selected['status'] == 'passed' and selected['scope'] == prepared['scope']
        selected['admission_command_id'] = json.loads((successor / 'successor-admit-command.json').read_bytes())['identity']['command_id']
    run_id = selected['run_id'] if selected else original['run_id']
    owners = json.loads((configuration / 'owners.json').read_bytes())['owners']
    authoring = (configuration / 'authoring-evidence.json').exists()
    owners = {name: value for name, value in owners.items() if authoring or name != 'registry'}
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    state, vault = LocalState.snapshot(root), (root / 'credentials.dpapi').read_bytes()
    routes = Routes.load(root)
    config = {'profile': 'local-gateway-v1', 'public_directory': str(public),
        'peers': {name: {'endpoint': routes.endpoint(name), 'token_env': 'AMPHORA_' + name.upper() + '_OPERATOR_TOKEN'}
                  for name in owners},
        'context': {'actor_id': 'admin', 'scope': prepared['scope'], 'run_id': run_id, 'synthetic': True},
        'launcher_key_env': 'AMPHORA_GATEWAY_SESSION_KEY'}
    gateway_config = write(output / 'gateway.json', config)
    owners['gateway'] = {'installation': str(ROOT.parent / '.test-results/local-gateway-drain-20261006a'),
        'source_lock': str(ROOT / 'services/local_gateway/uv.lock'), 'configuration': str(gateway_config),
        'secret_references': ['GATEWAY_SESSION_KEY'] + [name.upper() + '_OPERATOR_TOKEN' for name in config['peers']]}
    write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    records = json.loads((configuration / 'owner-readback.json').read_bytes())
    browser_input = write(output / 'browser-input.json', {'origin': routes.endpoint('gateway'),
        'run_id': run_id, 'scope': prepared['scope'], 'objective': prepared['objective'],
        'context': prepared['context'], 'records': records,
        'draft': json.loads((configuration / 'draft.json').read_bytes()) if authoring else None,
        'successor': selected, 'expected_nodes': selected['result']['node_count'] if selected else len(original['result']['graph']['nodes'])})
    tokens = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(['GATEWAY_SESSION_KEY'] + (['REGISTRY_OPERATOR_TOKEN'] if authoring else []) + (['RUNTIME_OPERATOR_TOKEN'] if selected else []))
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
    environment.update(PYTHONUTF8='1', AMPHORA_BROWSER_LAUNCH_KEY=tokens['GATEWAY_SESSION_KEY'])
    controller = BrowserController(root, output, routes, registry_token=tokens.get('REGISTRY_OPERATOR_TOKEN'))
    try:
        controller.start()
        if selected:
            for expected in (selected['result'], selected['predecessor']):
                code, observed = controller.request(routes.endpoint('runtime'), '/v3/graph-runs/' + expected['run_id'],
                    token=tokens['RUNTIME_OPERATOR_TOKEN'])
                assert code == 200 and observed == expected, 'Original run history changed after restart'
        script = 'successor_demo.mjs' if selected else 'local_demo.mjs'
        result = subprocess.run(['node', str(ROOT / 'studio/tests/integration' / script),
            str(browser_input), str(output)], cwd=ROOT / 'studio', env=environment,
            capture_output=True, text=True, encoding='utf-8', timeout=180,
            creationflags=subprocess.CREATE_NO_WINDOW)
        (output / 'browser.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        final = controller.drain()
        assert result.returncode == 0, 'Actual local browser acceptance failed; inspect browser.log'
        assert LocalState.snapshot(root) == state and (root / 'credentials.dpapi').read_bytes() == vault
        write(output / 'evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed', 'run_id': run_id, 'scope': prepared['scope'],
            'browser': json.loads((output / 'browser-evidence.json').read_bytes()), 'final': final,
            'assets': {name: hashlib.sha256((public / name).read_bytes()).hexdigest() for name in ('index.html', 'app.js', 'app.css')},
            'provider_calls': 0, 'workers_started': False,
            'limits': ['Actual localhost gateway/Studio and retained owners; synthetic science only',
                       'Immutable predecessor/successor readback; no new science or admission' if selected else
                       'Inspection and optional saved-draft validation; successor admission/trace remains separate']})
        print('Actual local browser execution/reasoning/context inspection passed; zero model calls', flush=True)
    finally:
        controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('configuration', 'retained', 'public', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--successor', type=Path)
    args = parser.parse_args()
    verify(*(getattr(args, name).absolute() for name in ('configuration', 'retained', 'public', 'output')),
           successor=args.successor.absolute() if args.successor else None)
