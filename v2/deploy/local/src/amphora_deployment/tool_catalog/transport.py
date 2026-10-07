"""Fixed loopback Registry heartbeat route, bounded response, no redirects/proxies."""

import http.client
import json

from ..profile import ProfileError, require


class HeartbeatTransport:
    def __init__(self, port, token):
        require(type(port) is int and 1 <= port <= 65535, 'heartbeat_port')
        require(type(token) is str and 16 <= len(token) <= 4096 and token.isascii()
                and all(32 < ord(char) < 127 for char in token), 'heartbeat_credential')
        self.port = port
        self._token = token

    def send(self, command):
        raw = json.dumps(command, sort_keys=True, separators=(',', ':')).encode()
        require(len(raw) <= 4096, 'heartbeat_request_size')
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=2)
        try:
            connection.request('POST', '/v1/registry/heartbeat', raw,
                {'Authorization': 'Bearer ' + self._token, 'Content-Type': 'application/json'})
            response = connection.getresponse()
            require(response.status == 200, 'heartbeat_http_failure')
            body = response.read(8193)
            require(len(body) <= 8192, 'heartbeat_response_size')
            return json.loads(body)
        except (OSError, http.client.HTTPException, ValueError):
            raise ProfileError('heartbeat_delivery_uncertain') from None
        finally:
            connection.close()
