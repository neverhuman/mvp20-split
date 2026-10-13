"""Test-owned three-owner lifecycle; no peer SQL or model credentials."""

import os
import subprocess
import sys
import urllib.request

from amphora_deployment.lifecycle import ProcessJob
from amphora_deployment.lifecycle.configuration import control_token
from local_demo_controller import Controller


class RecordsController(Controller):
    def __init__(self, root, output, routes, *, workers=False, model_key=None, deployment_python=None):
        self.routes, self.token = routes, control_token(root)
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        environment = {key: value for key, value in os.environ.items() if key.upper() in {
            'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
        environment['PYTHONUTF8'] = '1'
        if model_key is not None:
            assert workers and type(model_key) is str and model_key
            environment['AMPHORA_OPENAI_API_KEY'] = model_key
        self.job, self.process = ProcessJob(), None
        try:
            command = [str(deployment_python or sys.executable), '-I', '-m', 'amphora_deployment.lifecycle', 'serve',
                '--root', str(root), '--manifest', str(output / 'owners.json')]
            if workers:
                command += ['--workers-manifest', str(output / 'native.json')]
            self.process = subprocess.Popen(command, env=environment,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            self.job.attach(self.process)
            self.wait(lambda: self.control('/status'), timeout=60)
        except BaseException:
            self.close()
            raise

    def start(self):
        configured = self.control('/status')['owners']
        for owner in ('artifact', 'research', 'knowledge', 'planning', 'runtime'):
            if owner not in configured:
                continue
            self.control('/owners/' + owner + '/start', 'POST')
            path = '/ready' if owner in ('artifact', 'planning') else '/health'
            def ready(owner=owner, path=path):
                state = self.control('/status')['owners'][owner]
                assert state['state'] == 'running', 'Owner exited during startup: ' + owner
                return self.request(self.routes.endpoint(owner), path)[0] == 200
            self.wait(ready)

    def drain(self):
        configured = self.control('/status')
        for name in configured.get('workers', {}):
            self.control('/workers/' + name + '/quiesce', 'POST')
        self.wait(lambda: all(row['state'] == 'quiescent' for row in self.control('/status').get('workers', {}).values()))
        for owner in ('runtime', 'planning', 'knowledge', 'research', 'artifact'):
            if owner not in configured['owners']:
                continue
            self.control('/owners/' + owner + '/drain', 'POST')
        self.wait(lambda: all(row['state'] == 'exited' for row in self.control('/status')['owners'].values()))
        final = self.control('/status')
        assert all(row['exit_code'] == 0 for row in final['owners'].values())
        self.control('/shutdown', 'POST')
        assert self.process.wait(timeout=15) == 0
        return final
