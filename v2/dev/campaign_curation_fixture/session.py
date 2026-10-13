"""Owned actual supervisor session and bounded public HTTP; no peer SQL."""
import json
from contextlib import contextmanager
from urllib.error import HTTPError
from urllib.request import Request

from amphora_deployment.campaign_launch.credentials import launch_credential
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from campaign_launch_demo.controller import LaunchDemoController
from local_numeric_configuration import write


class PublicOwners:
    def __init__(self, controller, tokens, launch_port):
        self.controller, self.tokens = controller, tokens
        self.endpoints = {name: controller.routes.endpoint(name) for name in
                          ('runtime', 'artifact', 'registry', 'planning', 'knowledge', 'research')}
        self.endpoints['deployment'] = 'http://127.0.0.1:' + str(launch_port)

    def call(self, owner, path, body=None, *, method=None, allowed=(200,)):
        data = body if isinstance(body, bytes) else None if body is None else json.dumps(body).encode()
        request = Request(self.endpoints[owner] + path, data=data, method=method, headers={
            'Authorization': 'Bearer ' + self.tokens[owner], 'Content-Type': 'application/json'})
        try:
            response = self.controller.opener.open(request, timeout=20)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read(1048577)
            assert len(raw) <= 1048576
            value = json.loads(raw)
            assert response.status in allowed, f'{owner} {path}: HTTP {response.status}: {value}'
            return value


@contextmanager
def session(root, output, *, model_key=None):
    state = LocalState.snapshot(root)
    bundle = CredentialVault(root / 'credentials.dpapi', state['deployment_id']).load()
    names = ('runtime', 'artifact', 'registry', 'planning', 'knowledge', 'research')
    refs = bundle.environment([name.upper() + '_OPERATOR_TOKEN' for name in names])
    tokens = {name: refs[name.upper() + '_OPERATOR_TOKEN'] for name in names}
    tokens['deployment'] = launch_credential(root, state['deployment_id']).environment(['LAUNCH_GATEWAY_TOKEN'])['LAUNCH_GATEWAY_TOKEN']
    prepared = json.loads((output / 'launch-prepared.json').read_bytes())
    controller = LaunchDemoController(root, output, Routes.load(root), model_key=model_key)
    started = False
    try:
        controller.start_owners(tokens['registry']); started = True
        for name in controller.control('/status')['scientific_workers']:
            controller.control('/scientific-workers/' + name + '/standby', 'POST')
        yield PublicOwners(controller, tokens, prepared['launch_port'])
    finally:
        try:
            if started and controller.process.poll() is None:
                write(output / 'drain.json', {'status': 'drained', 'final': controller.drain()})
        finally:
            controller.close()
