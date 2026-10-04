"""Authenticated bounded metadata GET only; no retries, commands or peer imports."""

import http.client
import json
import socket
import threading
from urllib.parse import urlsplit

from ..context.policy import require
from ..context.snapshot import _constant, _object
from .targets import target


class MetadataTransport:
    def __init__(self, owner, endpoint, token):
        require(owner in {"registry", "runtime", "data"}, "metadata_owner")
        require(type(endpoint) is str and 1 <= len(endpoint) <= 512, "metadata_endpoint")
        try:
            parsed = urlsplit(endpoint)
            valid = (parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and parsed.port is not None and
                1 <= parsed.port <= 65535 and parsed.username is None and parsed.password is None and
                parsed.path in ("", "/") and not parsed.query and not parsed.fragment and
                not any(char.isspace() for char in endpoint))
        except ValueError:
            valid = False
        require(valid, "metadata_endpoint")
        require(type(token) is str and 32 <= len(token) <= 512 and all(33 <= ord(char) <= 126 for char in token), "metadata_credential")
        self.owner, self._host, self._port, self._token = owner, parsed.hostname, parsed.port, token

    def read(self, path, window):
        response_model = target(self.owner, path)
        require(window.owner == self.owner, "metadata_window")
        window.start()
        connection = http.client.HTTPConnection(self._host, self._port, timeout=window.remaining())
        timer = None
        try:
            connection.connect()
            active = connection.sock

            def expire():
                try:
                    active.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            timer = threading.Timer(window.remaining(), expire)
            timer.daemon = True
            timer.start()
            connection.request("GET", path, headers={"Authorization": "Bearer " + self._token})
            active.settimeout(window.remaining())
            response = connection.getresponse()
            require(response.status not in (401, 403), "metadata_denied")
            require(response.status != 404, "metadata_missing")
            require(response.status == 200, "metadata_unavailable")
            require(response.getheader("Content-Type", "").split(";", 1)[0].strip().lower() == "application/json", "metadata_media")
            chunks, size = [], 0
            while True:
                active.settimeout(window.remaining())
                part = response.read1(min(65536, 4194305 - size))
                size += len(part)
                window.consume(len(part))
                require(size <= 4194304, "metadata_response_limit")
                if not part:
                    break
                chunks.append(part)
                if response.isclosed():
                    break
            try:
                value = json.loads(b"".join(chunks).decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
                result = response_model.model_validate_json(json.dumps(value, allow_nan=False))
            except (ValueError, RecursionError):
                raise ValueError("metadata_protocol") from None
            window.remaining()
            return result
        except (OSError, http.client.HTTPException):
            raise ValueError("metadata_unavailable") from None
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()
