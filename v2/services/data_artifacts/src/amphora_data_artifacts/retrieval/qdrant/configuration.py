"""Pinned protocol identity separated from local endpoint and credentials."""

import math
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from amphora_contracts_core import SchemaRef

from ..validation import fingerprint, require

VERSION = "1.19.1"
IMAGE = "qdrant/qdrant@sha256:12364fe851b9f17356fc88189fc06d1b521262e04659ec7345975b00c9246a10"
OPENAPI_SHA256 = "eb3e5d71ba74e1d99124ca1a77d563bbfa47084f04a13ef9b197e339f5a4ce0a"


def backend_reference():
    descriptor = {
        "format": "data.qdrant-projection.v1",
        "server_version": VERSION,
        "image": IMAGE,
        "openapi_sha256": OPENAPI_SHA256,
        "distance": "Dot",
        "datatype": "float32",
        "point_limit": 256,
        "payload": "data.index-point.v1",
        "write_wait": True,
        "query_exact": True,
        "quantization": None,
    }
    return SchemaRef(schema_id="data.qdrant-projection", version="1", sha256=fingerprint(descriptor))


@dataclass(frozen=True, slots=True)
class QdrantConfiguration:
    endpoint: str
    token: str = field(repr=False)
    timeout: float = 5
    response_limit: int = 32 * 1024 * 1024

    def __post_init__(self):
        require(type(self.endpoint) is str, "qdrant_endpoint_required")
        value = urlsplit(self.endpoint)
        require(
            value.scheme == "http"
            and value.hostname == "127.0.0.1"
            and value.username is None
            and value.password is None
            and value.path in ("", "/")
            and not value.query
            and not value.fragment
            and value.port is not None
            and 1 <= value.port <= 65535,
            "qdrant_loopback_endpoint_required",
        )
        require(
            type(self.token) is str
            and 32 <= len(self.token) <= 512
            and all(33 <= ord(x) <= 126 for x in self.token),
            "qdrant_credential_required",
        )
        require(
            type(self.timeout) in (int, float) and math.isfinite(self.timeout) and 0.1 <= self.timeout <= 30,
            "qdrant_timeout_bound",
        )
        require(
            type(self.response_limit) is int and 1024 <= self.response_limit <= 32 * 1024 * 1024,
            "qdrant_response_bound",
        )

    @property
    def port(self):
        return urlsplit(self.endpoint).port

    @property
    def reference(self):
        return backend_reference()
