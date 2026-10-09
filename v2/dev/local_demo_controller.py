"""Owned subprocess/control helper for actual local demo probes; no execution authority."""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

from amphora_deployment.lifecycle import ProcessJob
from amphora_deployment.lifecycle.configuration import control_token


class Controller:
    def __init__(self, root, output, routes, label, *, model_key=None):
        self.routes, self.token = routes, control_token(root)
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        environment = {key: value for key, value in os.environ.items() if key.upper() in {
            'SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'COMSPEC'}}
        environment['PYTHONUTF8'] = '1'
        if model_key is not None:
            assert type(model_key) is str and model_key
            environment['AMPHORA_OPENAI_API_KEY'] = model_key
        self.job = ProcessJob()
        self.process = None
        try:
            self.process = subprocess.Popen([sys.executable, '-I', '-m', 'amphora_deployment.lifecycle', 'serve',
                '--root', str(root), '--manifest', str(output / 'owners.json'),
                '--tool-access-manifest', str(output / 'access.json'), '--workers-manifest', str(output / 'native.json'),
                '--scientific-manifest', str(output / (label + '-scientific.json')),
                '--catalog-manifest', str(output / (label + '-catalog.json'))], env=environment,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            self.job.attach(self.process)
            self.wait(lambda: self.control('/status'), timeout=60)
        except BaseException:
            self.close()
            raise

    def request(self, endpoint, path, *, token=None, body=None, method=None):
        data = body if type(body) is bytes else None if body is None else json.dumps(body).encode()
        headers = {'Content-Type': 'application/json'}
        if token is not None:
            headers['Authorization'] = 'Bearer ' + token
        request = urllib.request.Request(endpoint + path, data=data, method=method, headers=headers)
        try:
            response = self.opener.open(request, timeout=3)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read(1048577)
            assert len(raw) <= 1048576
            return response.status, json.loads(raw)

    def control(self, path, method='GET', allowed=(200,)):
        code, value = self.request(self.routes.endpoint('supervisor'), path, method=method, token=self.token)
        assert code in allowed, 'Unexpected controller response: ' + str(code) + ' ' + str(value.get('error'))
        return value

    def wait(self, predicate, *, timeout=60):
        deadline = time.monotonic() + timeout
        while True:
            try:
                result = predicate()
                if result:
                    return result
            except OSError:
                pass
            assert self.process.poll() is None and time.monotonic() < deadline, 'Local demo wait failed'
            time.sleep(.2)

    def start_owners(self, registry_token):
        configured = self.control('/status')['owners']
        for owner, path, token in [('artifact', '/ready', None), ('research', '/health', None),
                                  ('knowledge', '/health', None), ('planning', '/ready', None), ('runtime', '/health', None),
                                  ('registry', '/v1/releases', registry_token)]:
            if owner not in configured:
                continue
            self.control('/owners/' + owner + '/start', 'POST')
            self.wait(lambda owner=owner, path=path, token=token:
                      self.request(self.routes.endpoint(owner), path, token=token)[0] == 200)
            if owner in ('runtime', 'artifact'):
                self.control('/tool-access/' + owner + '/start', 'POST')

    def drain(self):
        status = self.control('/status')
        for name in status.get('workers', {}):
            self.control('/workers/' + name + '/quiesce', 'POST')
        for name in status.get('scientific_workers', {}):
            self.control('/scientific-workers/' + name + '/quiesce', 'POST')
        self.wait(lambda: all(not row['active_turn'] for row in self.control('/status')['scientific_workers'].values()))
        for name, row in self.control('/status')['scientific_workers'].items():
            if row['faulted']:
                self.control('/scientific-workers/' + name + '/recover', 'POST')
        self.wait(lambda: all(row['state'] == 'quiescent' for row in self.control('/status').get('workers', {}).values()))
        for owner in ('runtime', 'artifact'):
            self.control('/tool-access/' + owner + '/drain', 'POST')
        self.wait(lambda: all(row['state'] == 'drained' for row in self.control('/status')['tool_access'].values()))
        for owner in ('gateway', 'runtime', 'planning', 'knowledge', 'research', 'artifact', 'registry'):
            if owner not in status['owners']:
                continue
            def drained(owner=owner):
                value = self.control('/owners/' + owner + '/drain', 'POST', (200, 409))
                return 'error' not in value
            self.wait(drained)
        self.wait(lambda: all(row['state'] == 'exited' for row in self.control('/status')['owners'].values()))
        final = self.control('/status')
        assert all(row['exit_code'] == 0 for row in final['owners'].values())
        self.wait(lambda: self.control('/shutdown', 'POST', (200, 409)).get('state') == 'stopping')
        assert self.process.wait(timeout=15) == 0
        return final

    def close(self):
        self.job.close()
        if self.process is not None:
            self.process.wait(timeout=15)
