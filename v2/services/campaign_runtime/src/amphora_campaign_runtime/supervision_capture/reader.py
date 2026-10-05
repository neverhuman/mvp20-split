"""Two bounded owner reads, no redirects, proxies, retries or caller-selected URLs."""

import hashlib
import http.client
import json
import math
import socket
import threading
import time
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from amphora_contracts_core import ArtifactRef

from ..supervision_scope.observations import require


class CaptureUnavailable(ValueError):
    pass


@dataclass
class ReadWindow:
    seconds: float
    deadline: float = field(init=False)
    calls: int = field(default=0, init=False)
    consumed: int = field(default=0, init=False)

    def __post_init__(self):
        require(type(self.seconds) in (int, float) and math.isfinite(self.seconds) and 0 < self.seconds <= 10,
                'capture_deadline_configuration')
        self.deadline = time.monotonic() + self.seconds

    def remaining(self):
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise CaptureUnavailable('capture_deadline')
        return min(left, 5)

    def start(self):
        self.remaining()
        require(self.calls < 2, 'capture_call_limit')
        self.calls += 1

    def consume(self, size):
        self.remaining()
        self.consumed += size
        require(self.consumed <= 327680, 'capture_total_bytes')


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'capture_metadata_duplicate')
        result[key] = value
    return result


def constant(_value):
    raise ValueError('capture_metadata_nonfinite')


class CaptureReader:
    def __init__(self, endpoint, token, *, seconds=10):
        require(type(endpoint) is str and 1 <= len(endpoint) <= 512, 'capture_endpoint')
        try:
            parsed = urlsplit(endpoint)
            valid = (parsed.scheme == 'http' and parsed.hostname == '127.0.0.1' and
                     parsed.port is not None and 1 <= parsed.port <= 65535 and parsed.username is None and
                     parsed.password is None and parsed.path in ('', '/') and not parsed.query and
                     not parsed.fragment and not any(char.isspace() for char in endpoint))
        except ValueError:
            valid = False
        require(valid, 'capture_endpoint')
        require(type(token) is str and 32 <= len(token) <= 512 and
                all(33 <= ord(char) <= 126 for char in token), 'capture_credential')
        ReadWindow(seconds)
        self._host, self._port, self._token, self._seconds = parsed.hostname, parsed.port, token, seconds

    def fetch(self, reference):
        if reference is None:
            return None
        original = ArtifactRef.model_validate_json(reference.model_dump_json())
        require(original.size_bytes <= 65536, 'capture_size_limit')
        window = ReadWindow(self._seconds)
        path = '/v1/artifacts/' + original.artifact_id
        raw = self._read(path, window, limit=262144, metadata=True)
        try:
            data = json.loads(raw, object_pairs_hook=unique, parse_constant=constant)
            observed = ArtifactRef.model_validate_json(json.dumps(data, allow_nan=False))
        except (ValueError, RecursionError):
            raise CaptureUnavailable('capture_metadata_invalid') from None
        require(observed == original, 'capture_metadata_mismatch')
        content = self._read(path + '/processing-content', window, limit=original.size_bytes, metadata=False)
        require(len(content) == original.size_bytes and hashlib.sha256(content).hexdigest() == original.sha256,
                'capture_content_mismatch')
        return content

    def _read(self, path, window, *, limit, metadata):
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

            timer = threading.Timer(max(0, window.deadline - time.monotonic()), expire)
            timer.daemon = True
            timer.start()
            connection.request('GET', path, headers={'Authorization': 'Bearer ' + self._token})
            active.settimeout(window.remaining())
            response = connection.getresponse()
            if response.status in (401, 403):
                raise CaptureUnavailable('capture_processing_denied')
            if response.status == 404:
                raise CaptureUnavailable('capture_unavailable')
            if response.status != 200:
                raise CaptureUnavailable('capture_peer_unavailable')
            require(response.getheader('Content-Encoding', 'identity') == 'identity', 'capture_encoding')
            if metadata:
                require(response.getheader('Content-Type', '').split(';', 1)[0].strip().lower() == 'application/json',
                        'capture_metadata_type')
            chunks, size = [], 0
            while True:
                active.settimeout(window.remaining())
                block = response.read1(min(65536, limit + 1 - size))
                window.consume(len(block))
                size += len(block)
                require(size <= limit, 'capture_response_limit')
                if not block:
                    break
                chunks.append(block)
                if response.isclosed():
                    break
            return b''.join(chunks)
        except (OSError, http.client.HTTPException):
            raise CaptureUnavailable('capture_peer_unavailable') from None
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()
