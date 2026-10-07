"""Read the actual Registry deployment before advertising its pinned executor."""

import http.client
import json

from ..profile import require

CAPABILITIES = {**{'evolution-' + name: 'numeric.search-' + name for name in ('seed', 'requests', 'collect', 'vary')},
                'synthetic-objectives': 'synthetic.numeric-objectives',
                'synthetic-objectives-rebuilt': 'synthetic.numeric-objectives'}


class CatalogTarget:
    def __init__(self, replica, profile, port, token):
        require(type(port) is int and 1024 <= port <= 65535, 'catalog_target_port')
        require(type(token) is str and token.isascii() and 16 <= len(token) <= 4096
                and all(32 < ord(char) < 127 for char in token), 'catalog_target_credential')
        self.replica, self.profile, self.port, self._token = replica, profile, port, token

    def matches(self, value):
        if type(value) is not dict or value.get('scope') != self.replica.scope or value.get('status') != 'active':
            return False
        deployment = value.get('deployment')
        if type(deployment) is not dict:
            return False
        release = deployment.get('release')
        if type(release) is not dict or type(release.get('tool')) is not dict:
            return False
        tool = release['tool']
        workers = deployment.get('workers')
        return (deployment.get('deployment_id') == self.replica.deployment_id
            and deployment.get('architecture') == 'x86_64' and deployment.get('operating_system') == 'linux'
            and type(workers) is list and self.replica.worker_id in workers
            and tool.get('capability_id') == CAPABILITIES[self.profile.name]
            and tool.get('image_sha256') == self.profile.image_id[7:] and tool.get('contract_version') == '1')

    def __call__(self):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=1)
        try:
            connection.request('GET', '/v1/deployments/' + self.replica.deployment_id,
                               headers={'Authorization': 'Bearer ' + self._token})
            response = connection.getresponse()
            require(response.status == 200, 'catalog_target_http')
            body = response.read(8193)
            require(len(body) <= 8192, 'catalog_target_size')
            return self.matches(json.loads(body))
        finally:
            connection.close()
