"""Public Runtime routes over fixed loopback HTTP; no redirects or ambient proxies."""
import http.client
import json
from urllib.parse import quote

from amphora_contracts_graph_runtime import GraphRunPage
from amphora_contracts_runtime import CommandReceipt

from .intent import LaunchError
from .ports import PeerUnavailable


class RuntimePeer:
    def __init__(self, port: int, token: str):
        if (type(port) is not int or not 1024 <= port <= 65535
                or type(token) is not str or not 16 <= len(token) <= 4096
                or not all(32 < ord(char) < 127 for char in token)):
            raise LaunchError('launch_peer_configuration_invalid')
        self.port, self._token = port, token

    def request(self, method, path, raw=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        try:
            connection.request(method, path, raw, {
                'Authorization': 'Bearer ' + self._token, 'Content-Type': 'application/json'})
            response = connection.getresponse()
            body = response.read(262145)
            if len(body) > 262144:
                raise LaunchError('launch_peer_response_invalid')
            if response.status >= 500 or response.status in {408, 425, 429}:
                raise PeerUnavailable()
            return response.status, body
        except (OSError, http.client.HTTPException):
            raise PeerUnavailable() from None
        finally:
            connection.close()

    @staticmethod
    def _parse(status, raw, model):
        if status != 200:
            # Includes redirects/auth failures. Never turn an HTTP failure into
            # an admission rejection; only Runtime's bound receipt can do that.
            raise LaunchError('launch_peer_response_invalid')
        try:
            return model.model_validate_json(raw)
        except ValueError:
            raise LaunchError('launch_peer_response_invalid') from None

    def receipt(self, intent):
        identity = intent.admission.identity
        path = '/v1/commands/graph.admit_draft/' + quote(identity.command_id, safe='')
        path += '?actor_id=' + quote(identity.actor_id, safe='')
        status, raw = self.request('GET', path)
        if status == 404:
            try:
                record = json.loads(raw)
            except ValueError:
                raise LaunchError('launch_peer_response_invalid') from None
            if type(record) is dict and record.get('reason_code') == 'receipt_unavailable':
                return None
        return self._parse(status, raw, CommandReceipt)

    def admit(self, intent):
        status, raw = self.request('POST', '/v1/graph-runs/drafts', intent.admission.canonical_bytes)
        return self._parse(status, raw, CommandReceipt)

    def run(self, state):
        if state.run_id is None:
            raise LaunchError('launch_admission_required')
        status, raw = self.request('GET', '/v1/graph-runs/' + quote(state.run_id, safe='') + '?limit=1')
        return self._parse(status, raw, GraphRunPage)
