"""Explicit loopback Data reads with a whole-review deadline, no retries."""

import http.client
import json
import re
import socket
import threading
import time
from urllib.parse import urlsplit

from amphora_contracts_core import ArtifactRef
from amphora_contracts_evidence import ConversionTrace, SourceRevision

from ..context.policy import require
from ..context.snapshot import _constant, _object
from .budget import SourceUnavailable

IDENTIFIER = r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"
PATH = re.compile(r"/v1/(?:artifacts/" + IDENTIFIER + r"(?:/processing-content)?|acquisition/(?:sources/" +
                  IDENTIFIER + "/" + IDENTIFIER + "|traces/" + IDENTIFIER + "))")


class DataReader:
    def __init__(self, endpoint, token):
        require(type(endpoint) is str and 1 <= len(endpoint) <= 512, "source_peer_endpoint")
        try:
            parsed = urlsplit(endpoint)
            valid = (parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and
                     parsed.port is not None and 1 <= parsed.port <= 65535 and
                     parsed.username is None and parsed.password is None and parsed.path in ("", "/") and
                     not parsed.query and not parsed.fragment and not any(char.isspace() for char in endpoint))
        except ValueError:
            valid = False
        require(valid, "source_peer_endpoint")
        require(type(token) is str and 32 <= len(token) <= 512 and
                all(33 <= ord(char) <= 126 for char in token), "source_peer_credential")
        self._host, self._port, self._token = parsed.hostname, parsed.port, token

    def read(self, path, budget, *, limit=262144, json_body=True):
        require(type(path) is str and PATH.fullmatch(path) is not None, "source_peer_path")
        require(type(limit) is int and 0 <= limit <= 4194304, "source_peer_response_limit")
        budget.start()
        connection = http.client.HTTPConnection(self._host, self._port, timeout=budget.remaining())
        timer = None
        try:
            connection.connect()
            active_socket = connection.sock

            def expire():
                try:
                    active_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            timer = threading.Timer(max(0, budget.deadline - time.monotonic()), expire)
            timer.daemon = True
            timer.start()
            connection.request("GET", path, headers={"Authorization": "Bearer " + self._token})
            active_socket.settimeout(budget.remaining())
            response = connection.getresponse()
            if response.status in (401, 403):
                raise ValueError("source_access_denied")
            if response.status == 404:
                raise ValueError("source_reference_unavailable")
            if response.status != 200:
                raise SourceUnavailable("source_peer_unavailable")
            if json_body and response.getheader("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                raise SourceUnavailable("source_peer_protocol")
            chunks, size = [], 0
            while True:
                active_socket.settimeout(budget.remaining())
                block = response.read1(min(65536, limit + 1 - size))
                budget.consume(len(block))
                size += len(block)
                require(size <= limit, "source_peer_response_limit")
                if not block:
                    break
                chunks.append(block)
                if response.isclosed():
                    break
            return b"".join(chunks)
        except (OSError, http.client.HTTPException):
            raise SourceUnavailable("source_peer_unavailable") from None
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()

    def record(self, path, model, budget):
        raw = self.read(path, budget)
        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
            return model.model_validate_json(json.dumps(value, allow_nan=False))
        except (ValueError, RecursionError):
            raise SourceUnavailable("source_peer_protocol") from None

    def artifact(self, reference, budget):
        return self.record(f"/v1/artifacts/{reference.artifact_id}", ArtifactRef, budget)

    def content(self, reference, budget):
        return self.read(f"/v1/artifacts/{reference.artifact_id}/processing-content", budget,
                         limit=reference.size_bytes, json_body=False)

    def source(self, reference, budget):
        return self.record(f"/v1/acquisition/sources/{reference.source_id}/{reference.revision_id}",
                           SourceRevision, budget)

    def trace(self, reference, budget):
        return self.record(f"/v1/acquisition/traces/{reference.trace_id}", ConversionTrace, budget)
