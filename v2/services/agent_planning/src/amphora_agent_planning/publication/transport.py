"""Publication-only SDK transport with a wall-clock bound on each exchange."""

import http.client
import json
import math
import re
import socket
import threading
import time
from urllib.parse import urlsplit

from amphora_tool_protocol import ProtocolError, Reply, TransportLost

from ..context.snapshot import _constant, _object

ID = r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"
ROUTES = {
    "GET": re.compile(r"/v1/(?:commands/artifacts\.(?:begin_derived_upload|finalize)/" + ID +
                      r"|artifacts/" + ID + r"/derivation)"),
    "POST": re.compile(r"/v1/(?:derived-uploads|artifacts/finalize)"),
    "PUT": re.compile(r"/v1/uploads/" + ID + r"/content"),
}


def check(condition, reason):
    if not condition:
        raise ProtocolError(reason)


class PublicationTransport:
    def __init__(self, endpoint, token, *, seconds=5):
        check(type(endpoint) is str and 1 <= len(endpoint) <= 512, "publication_endpoint")
        try:
            parsed = urlsplit(endpoint)
            valid = (parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and
                     parsed.port is not None and 1 <= parsed.port <= 65535 and
                     parsed.username is None and parsed.password is None and parsed.path in ("", "/") and
                     not parsed.query and not parsed.fragment and not any(c.isspace() for c in endpoint))
        except ValueError:
            valid = False
        check(valid, "publication_endpoint")
        check(type(token) is str and 32 <= len(token) <= 512 and all(33 <= ord(c) <= 126 for c in token),
              "publication_credential")
        check(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= 5,
              "publication_transport_deadline")
        self._host, self._port, self._token, self.seconds = parsed.hostname, parsed.port, token, seconds

    def request(self, method, path, body=None, *, limit=262144, media_type="application/json"):
        check(type(method) is str and method in ROUTES and type(path) is str and
              ROUTES[method].fullmatch(path) is not None, "publication_path")
        check(type(limit) is int and 0 <= limit <= 262144, "publication_response_limit")
        check(media_type == "application/json", "publication_media_type")
        check((method == "GET" and body is None) or
              (method != "GET" and type(body) is bytes and 0 < len(body) <= 1048576), "publication_request_limit")
        deadline = time.monotonic() + self.seconds
        connection = http.client.HTTPConnection(self._host, self._port, timeout=self.seconds)
        timer = None
        try:
            connection.connect()
            active_socket = connection.sock

            def expire():
                try:
                    active_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            timer = threading.Timer(max(0, deadline - time.monotonic()), expire)
            timer.daemon = True
            timer.start()
            connection.request(method, path, body, {"Authorization": "Bearer " + self._token,
                                                   "Content-Type": media_type})
            response = connection.getresponse()
            chunks, size = [], 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TransportLost("publication_transport_lost")
                active_socket.settimeout(remaining)
                chunk = response.read1(min(65536, limit + 1 - size))
                size += len(chunk)
                check(size <= limit, "publication_response_limit")
                if not chunk:
                    break
                chunks.append(chunk)
                if response.isclosed():
                    break
            if time.monotonic() >= deadline:
                raise TransportLost("publication_transport_lost")
            payload = b"".join(chunks)
            if response.status == 200:
                check(response.getheader("Content-Type", "").split(";", 1)[0].strip().lower() == "application/json",
                      "publication_response_media")
                try:
                    json.loads(payload.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
                except (ValueError, RecursionError):
                    raise ProtocolError("publication_response_json") from None
            return Reply(response.status, payload)
        except (OSError, http.client.HTTPException):
            raise TransportLost("publication_transport_lost") from None
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()
