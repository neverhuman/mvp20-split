"""Owner-local bounded POST read transport; compiled catalogs, no writes/retries."""

import http.client
import json
import socket
import threading
from urllib.parse import urlsplit

from ..context.policy import require
from ..context.snapshot import _constant, _object
from .profile import PeerUnavailable


def canonical(record):
    return json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


class BoundedReadTransport:
    def __init__(self, endpoint, token, profile):
        self.profile = profile
        require(type(endpoint) is str and 1 <= len(endpoint) <= 512, self.profile.code('peer_endpoint'))
        try:
            parsed = urlsplit(endpoint)
            valid = (parsed.scheme == 'http' and parsed.hostname == '127.0.0.1' and
                     parsed.port is not None and 1 <= parsed.port <= 65535 and
                     parsed.username is None and parsed.password is None and parsed.path in ('', '/') and
                     not parsed.query and not parsed.fragment and not any(c.isspace() for c in endpoint))
        except ValueError:
            valid = False
        require(valid, self.profile.code('peer_endpoint'))
        require(type(token) is str and 32 <= len(token) <= 512 and all(33 <= ord(c) <= 126 for c in token),
                self.profile.code('peer_credential'))
        self._host, self._port, self._token = parsed.hostname, parsed.port, token

    def read(self, path, reference, window):
        require(type(path) is str and path in self.profile.routes, self.profile.code('peer_path'))
        require(window.profile == self.profile, self.profile.code("read_profile_mismatch"))
        request_model, response_model, limit = self.profile.routes[path]
        reference = request_model.model_validate_json(reference.model_dump_json(warnings=False))
        body = canonical(reference)
        require(len(body) <= 4096, self.profile.code('request_size'))
        window.start()
        connection = http.client.HTTPConnection(self._host, self._port, timeout=window.remaining())
        timer = None
        try:
            connection.connect()
            active_socket = connection.sock

            def expire():
                try:
                    active_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            timer = threading.Timer(window.remaining(), expire)
            timer.daemon = True
            timer.start()
            connection.request('POST', path, body, {'Authorization': 'Bearer ' + self._token,
                                                   'Content-Type': 'application/json'})
            active_socket.settimeout(window.remaining())
            response = connection.getresponse()
            if response.status in (401, 403):
                raise ValueError(self.profile.code('access_denied'))
            if response.status == 404:
                raise ValueError(self.profile.code('reference_unavailable'))
            if response.status != 200:
                raise PeerUnavailable(self.profile.code('peer_unavailable'))
            require(response.getheader('Content-Type', '').split(';', 1)[0].strip().lower() == 'application/json',
                    self.profile.code('peer_media'))
            chunks, size = [], 0
            while True:
                active_socket.settimeout(window.remaining())
                chunk = response.read1(min(65536, limit + 1 - size))
                size += len(chunk)
                window.consume(len(chunk))
                require(size <= limit, self.profile.code('response_limit'))
                if not chunk:
                    break
                chunks.append(chunk)
                if response.isclosed():
                    break
            window.remaining()
            try:
                value = json.loads(b''.join(chunks).decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
                record = response_model.model_validate_json(json.dumps(value, allow_nan=False))
            except (ValueError, RecursionError):
                raise PeerUnavailable(self.profile.code('peer_protocol')) from None
            window.remaining()
            return record
        except (OSError, http.client.HTTPException):
            raise PeerUnavailable(self.profile.code('peer_unavailable')) from None
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()
