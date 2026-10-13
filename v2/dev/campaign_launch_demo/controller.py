"""One installed supervisor process; uses only Deployment's operator control API."""
import json
import os
import subprocess
import urllib.request

from amphora_deployment.lifecycle import ProcessJob
from amphora_deployment.lifecycle.configuration import control_token
from local_demo_controller import Controller


class LaunchDemoController(Controller):
    def __init__(self, root, output, routes, *, model_key=None):
        self.routes, self.token = routes, control_token(root)
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        prepared = json.loads((output / 'launch-prepared.json').read_bytes())
        environment = {key: value for key, value in os.environ.items() if key.upper() in {
            'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
        environment['PYTHONUTF8'] = '1'
        if model_key is not None:
            assert type(model_key) is str and model_key
            environment['AMPHORA_OPENAI_API_KEY'] = model_key
        self.job, self.process = ProcessJob(), None
        try:
            with (output / 'supervisor.log').open('ab') as log:
                self.process = subprocess.Popen([prepared['deployment_python'], '-I', '-m', 'amphora_deployment.lifecycle', 'serve',
                    '--root', str(root), '--manifest', str(output / 'owners.json'),
                    '--tool-access-manifest', str(output / 'access.json'), '--workers-manifest', str(output / 'native.json'),
                    '--launch-manifest', str(output / 'launch.json'), '--launch-port', str(prepared['launch_port'])],
                    env=environment, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
            self.job.attach(self.process)
            self.wait(lambda: self.control('/status'), timeout=60)
        except BaseException:
            self.close()
            raise

    def start_owners(self, registry_token):
        super().start_owners(registry_token)
        self.control('/owners/gateway/start', 'POST')
        def ready():
            with self.opener.open(self.routes.endpoint('gateway') + '/', timeout=3) as response:
                return response.status == 200
        self.wait(ready)
