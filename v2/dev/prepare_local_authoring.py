"""Publish an explicitly fixture-authored draft through Runtime; preserve campaign history."""

import argparse
import json
import os
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState

from local_authoring_controller import AuthoringController
from local_numeric_configuration import write


def prepare(source, output, *, resume=False):
    if not resume:
        output.mkdir(parents=True, exist_ok=False)
        for path in source.glob('*.json'):
            shutil.copyfile(path, output / path.name)
    else:
        assert (output / 'draft-save-command.json').is_file(), 'Original command required for resume'
    owners = json.loads((output / 'owners.json').read_bytes())['owners']
    configuration = json.loads((output / 'runtime.json').read_bytes())
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    state, vault = LocalState.snapshot(root), (root / 'credentials.dpapi').read_bytes()
    routes = Routes.load(root)
    scope = json.loads((output / 'prepared.json').read_bytes())['scope']
    configuration['authoring'] = True
    for principal in configuration['principals']:
        if principal['actor_id'] == 'admin':
            principal['actions'] = sorted(set(principal['actions']) | {'author', 'validate'})
    if not resume:
        owners['runtime']['configuration'] = str(write(output / 'runtime.json', configuration))
        write(output / 'owners.json', {'profile': 'local-supervisor-v1', 'owners': owners})
    tokens = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load().environment(
        ['RUNTIME_OPERATOR_TOKEN', 'REGISTRY_OPERATOR_TOKEN'])
    controller = AuthoringController(root, output, routes, registry_token=tokens['REGISTRY_OPERATOR_TOKEN'])
    try:
        controller.start()
        def call(path, body=None):
            status, value = controller.request(routes.endpoint('runtime'), path,
                token=tokens['RUNTIME_OPERATOR_TOKEN'], body=body)
            assert status == 200, 'Public Runtime authoring failed: ' + str(status)
            return value
        identity = {'scope': scope, 'actor_id': 'admin', 'command_id': uuid.uuid4().hex,
                    'command_family': 'definition.save'}
        draft_id = 'demo-numeric-' + uuid.uuid4().hex
        command = {'encoding': 'amphora-command-v2', 'identity': identity, 'payload': {
            'draft_id': draft_id, 'expected_revision': 0,
            'title': 'Synthetic numeric campaign (engineering fixture)',
            'definition': json.loads((output / 'graph.json').read_bytes())}}
        if resume:
            command = json.loads((output / 'draft-save-command.json').read_bytes())
            draft_id = command['payload']['draft_id']
        else:
            write(output / 'draft-save-command.json', command)
        receipt = call('/v1/definition-drafts/save', command)
        if resume:
            assert receipt == json.loads((output / 'draft-save-receipt.json').read_bytes())
        else:
            write(output / 'draft-save-receipt.json', receipt)
        assert receipt['outcome']['status'] == 'accepted'
        draft = call('/v1/definition-drafts/' + draft_id)
        write(output / 'draft.json', draft)
        # Normalize the request with the independently installed public DTO, not peer state.
        runtime_python = Path(owners['runtime']['installation']) / 'environment/Scripts/python.exe'
        environment = {key: value for key, value in os.environ.items() if key.upper() in {
            'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
        environment['PYTHONUTF8'] = '1'
        normalized = subprocess.run([str(runtime_python), '-I', '-c',
            'import sys; from amphora_contracts_campaigns import ExecutableCampaignV4; '
            'print(ExecutableCampaignV4.model_validate_json(sys.stdin.buffer.read()).model_dump_json())'],
            input=json.dumps(command['payload']['definition']).encode(), capture_output=True,
            env=environment, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
        assert normalized.returncode == 0, 'Public definition normalization failed'
        assert draft['definition'] == json.loads(normalized.stdout)
        assert draft['head']['revision'] == 1
        assert draft['scope'] == scope and draft['head']['title'] == command['payload']['title']
        assert call('/v1/definition-drafts/save', command) == receipt
        write(output / 'draft.json', draft)
        final = controller.drain()
        assert LocalState.snapshot(root) == state and (root / 'credentials.dpapi').read_bytes() == vault
        write(output / 'authoring-evidence.json', {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'passed', 'draft': draft['head'], 'scope': scope, 'receipt': receipt, 'final': final,
            'provider_calls': 0, 'workers_started': False,
            'limits': ['Fixture-authored copy, not model-authored topology or a successor admission',
                       'Original campaign/configuration/history preserved; no scientific validation']})
        print('Scoped fixture draft published; exact receipt replay; zero workers/model calls', flush=True)
    finally:
        controller.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--resume', action='store_true', help='Replay the original saved command in an existing preparation')
    args = parser.parse_args()
    prepare(args.source.absolute(), args.output.absolute(), resume=args.resume)
