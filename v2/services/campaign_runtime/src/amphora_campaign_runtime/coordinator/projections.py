"""Bounded public Artifact reads occur outside Runtime transactions and grants."""

import hashlib
import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from amphora_contracts_core import ArtifactRef

from .values import ensure


class ProjectionUnavailable(RuntimeError):
    """Transport uncertainty leaves the stable advance command pending for retry."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_key")
        result[key] = value
    return result


def _nonfinite(_value):
    raise ValueError("nonfinite_json")


class ArtifactProjections:
    def __init__(self, endpoint, token, *, maximum_bytes=262144):
        parsed = urlsplit(endpoint)
        if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or
            parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "::1"})):
            raise ValueError("Explicit artifact HTTP endpoint required")
        if not isinstance(token, str) or len(token) < 32 or type(maximum_bytes) is not int or not 1 <= maximum_bytes <= 1048576:
            raise ValueError("Bounded projection bytes and configured credential required")
        self.endpoint, self.token, self.maximum_bytes = endpoint.rstrip("/"), token, maximum_bytes

    def _read(self, path, maximum):
        request = Request(self.endpoint + path, headers={"Authorization": "Bearer " + self.token})
        try:
            with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=10) as response:
                body = response.read(maximum + 1)
            ensure(len(body) <= maximum, "projection_payload_too_large")
            return body
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            raise ProjectionUnavailable("artifact_projection_unavailable") from error

    def fetch(self, artifact):
        ensure(artifact.media_type == "application/json" and artifact.size_bytes <= self.maximum_bytes,
               "projection_payload_unsupported")
        metadata = self._read("/v1/artifacts/" + artifact.artifact_id, 16384)
        try:
            observed = ArtifactRef.model_validate_json(metadata)
        except ValueError as error:
            raise ProjectionUnavailable("artifact_metadata_invalid") from error
        ensure(observed == artifact, "projection_artifact_binding_mismatch")
        body = self._read("/v1/artifacts/" + artifact.artifact_id + "/content", self.maximum_bytes)
        ensure(len(body) == artifact.size_bytes and hashlib.sha256(body).hexdigest() == artifact.sha256, "projection_artifact_integrity")
        try:
            return json.loads(body, object_pairs_hook=_pairs, parse_float=Decimal, parse_constant=_nonfinite)
        except (ValueError, RecursionError) as error:
            from ..lifecycle.model import TransitionError
            raise TransitionError("projection_artifact_json_invalid") from error
