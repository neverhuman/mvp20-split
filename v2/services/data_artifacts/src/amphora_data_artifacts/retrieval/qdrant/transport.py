"""Authenticated bounded HTTP with an absolute socket deadline and safe errors."""

import http.client
import json
import math
import re
import socket
import time
from threading import Timer

from ..validation import RetrievalError, require
from .configuration import VERSION, QdrantConfiguration


class QdrantError(RetrievalError):
    pass


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise QdrantError("qdrant_duplicate_key")
        result[key] = value
    return result


def constant(_value):
    raise QdrantError("qdrant_nonfinite_json")


def finite_number(value):
    result = float(value)
    if not math.isfinite(result):
        raise QdrantError("qdrant_nonfinite_json")
    return result


def interrupt(sock):
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass


def bounded_json(value):
    stack = [(iter((value,)), 0)]
    visited = 0
    while stack:
        iterator, depth = stack[-1]
        try:
            item = next(iterator)
        except StopIteration:
            stack.pop()
            continue
        visited += 1
        if visited > 2_000_000:
            raise QdrantError("qdrant_json_node_bound")
        if type(item) in (dict, list):
            if depth >= 64:
                raise QdrantError("qdrant_json_depth")
            stack.append((iter(item.values() if type(item) is dict else item), depth + 1))


class QdrantTransport:
    def __init__(self, configuration):
        require(type(configuration) is QdrantConfiguration, "qdrant_configuration_required")
        self.configuration = configuration

    def request(self, method, path, body=None, *, allow_missing=False):
        require(method in {"GET", "PUT", "POST"}, "qdrant_method_required")
        require(
            type(path) is str
            and (
                path == "/"
                or re.fullmatch(
                    r"/collections/amphora_[0-9a-f]{64}(?:/points(?:/(?:scroll|query))?)?(?:\?wait=true)?",
                    path,
                )
            ),
            "qdrant_owned_path_required",
        )
        require(type(allow_missing) is bool, "qdrant_missing_policy")
        try:
            bounded_json(body)
            raw = None if body is None else json.dumps(body, separators=(",", ":"), allow_nan=False).encode()
        except (ValueError, TypeError, RecursionError) as error:
            raise QdrantError("qdrant_request_shape") from error
        require(raw is None or len(raw) <= 32 * 1024 * 1024, "qdrant_request_bound")
        config = self.configuration
        connection = http.client.HTTPConnection("127.0.0.1", config.port, timeout=config.timeout)
        deadline = time.monotonic() + config.timeout
        timer = None
        try:
            connection.connect()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise QdrantError("qdrant_timeout")
            timer = Timer(remaining, interrupt, args=(connection.sock,))
            timer.daemon = True
            timer.start()
            connection.request(
                method,
                path,
                body=raw,
                headers={
                    "api-key": config.token,
                    "Content-Type": "application/json",
                    "Accept-Encoding": "identity",
                },
            )
            response = connection.getresponse()
            if response.status in (401, 403):
                raise QdrantError("qdrant_access_denied")
            if response.status == 404 and allow_missing:
                return None
            if response.status != 200:
                raise QdrantError("qdrant_http_" + str(response.status))
            if response.getheader("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                raise QdrantError("qdrant_content_type")
            if response.getheader("Content-Encoding", "identity") != "identity":
                raise QdrantError("qdrant_content_encoding")
            chunks, count = [], 0
            while True:
                if time.monotonic() >= deadline:
                    raise QdrantError("qdrant_timeout")
                chunk = response.read1(min(65536, config.response_limit + 1 - count))
                if not chunk:
                    break
                chunks.append(chunk)
                count += len(chunk)
                if count > config.response_limit:
                    raise QdrantError("qdrant_response_bound")
            if time.monotonic() >= deadline:
                raise QdrantError("qdrant_timeout")
            if response.length not in (None, 0):
                raise QdrantError("qdrant_truncated_response")
            raw = b"".join(chunks)
        except (OSError, http.client.HTTPException) as error:
            code = "qdrant_timeout" if time.monotonic() >= deadline else "qdrant_unavailable"
            raise QdrantError(code) from error
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()
        try:
            result = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=unique,
                parse_constant=constant,
                parse_float=finite_number,
            )
        except QdrantError:
            raise
        except (ValueError, RecursionError) as error:
            raise QdrantError("qdrant_response_shape") from error
        if type(result) is not dict:
            raise QdrantError("qdrant_response_shape")
        bounded_json(result)
        return result

    def server(self):
        result = self.request("GET", "/")
        require(result.get("version") == VERSION, "qdrant_version_mismatch")
        self.request("GET", "/collections/amphora_" + "0" * 64, allow_missing=True)
        return result
