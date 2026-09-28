"""Upload identity, capacity and content policy values."""

import hashlib
import json
import math
from dataclasses import dataclass

from amphora_contracts_artifacts import ContentDescriptor
from amphora_contracts_core import Scope


class UploadError(ValueError):
    """Reason-only safe error, never source bytes, paths or credentials."""


@dataclass(frozen=True, slots=True)
class Principal:
    actor_id: str
    scope: Scope
    actions: frozenset[str]

    def require(self, action, identity=None):
        if action not in self.actions:
            raise UploadError("access_denied")
        if identity is not None and (identity.scope != self.scope or identity.actor_id != self.actor_id):
            raise UploadError("access_denied")

    @property
    def bindings(self):
        return {"tenant": self.scope.tenant_id, "project": self.scope.project_id, "actor": self.actor_id}


@dataclass(frozen=True, slots=True)
class UploadLimits:
    max_bytes: int = 16 * 1024 * 1024
    scope_bytes: int = 256 * 1024 * 1024
    streams: int = 2
    uploads: int = 1024
    attempts: int = 8
    seconds: int = 300

    def __post_init__(self):
        if any(type(v) is not int or v < 1 for v in (
            self.max_bytes, self.scope_bytes, self.streams, self.uploads, self.attempts, self.seconds
        )):
            raise ValueError("Positive bounded upload limits required")
        if max(self.max_bytes, self.scope_bytes) > 9007199254740991 or self.seconds > 3600:
            raise ValueError("Upload limits exceed supported profile")


@dataclass(frozen=True, slots=True)
class ContentPolicy:
    # Exact media/schema pairs supplied by trusted deployment policy, never by request.
    allowed: frozenset[tuple[str, str, str, str]]

    # Narrow registered fixture schemas; arbitrary schema IDs/hashes do not install validators.
    SCHEMAS = {
        "application/octet-stream": b'{"type":"string","contentEncoding":"base64"}',
        "text/plain": b'{"type":"string"}',
        "application/json": b'{"type":"object"}',
    }

    def __post_init__(self):
        for media, _identifier, version, digest in self.allowed:
            if (media not in self.SCHEMAS or version != "1"
                or hashlib.sha256(self.SCHEMAS[media]).hexdigest() != digest):
                raise ValueError("Only registered fixture schema validators are supported")

    def admit(self, descriptor: ContentDescriptor, limits: UploadLimits):
        schema = descriptor.schema_ref
        if (descriptor.media_type, schema.schema_id, schema.version, schema.sha256) not in self.allowed:
            raise UploadError("unsupported_content")
        if descriptor.size_bytes > limits.max_bytes:
            raise UploadError("upload_too_large")

    def validate(self, descriptor, payload):
        """Exact admitted schema identity plus its actual bounded content validator."""
        if descriptor.media_type == "application/octet-stream":
            return
        try:
            value = payload.decode("utf-8")
            if descriptor.media_type == "application/json":
                def unique(pairs):
                    result = {}
                    for key, item in pairs:
                        key.encode("utf-8")
                        if key in result:
                            raise ValueError("Duplicate JSON key")
                        result[key] = item
                    return result

                def invalid_constant(_value):
                    raise ValueError("Non-finite JSON constant")

                value = json.loads(value, object_pairs_hook=unique, parse_constant=invalid_constant)
                if not isinstance(value, dict):
                    raise ValueError("Object required")
                pending = [(value, 1)]
                while pending:
                    item, depth = pending.pop()
                    if depth > 64:
                        raise ValueError("Content nesting exceeded")
                    if isinstance(item, dict):
                        pending.extend((v, depth + 1) for v in item.values())
                    elif isinstance(item, list):
                        pending.extend((v, depth + 1) for v in item)
                    elif isinstance(item, float) and not math.isfinite(item):
                        raise ValueError("Non-finite JSON number")
                    elif isinstance(item, str):
                        item.encode("utf-8")
        except (ValueError, UnicodeError, RecursionError) as error:
            raise UploadError("content_schema_mismatch") from error


@dataclass(frozen=True, slots=True)
class UploadAttempt:
    upload_id: str
    attempt_id: str
    generation: int
    storage_key: str
    content: ContentDescriptor


@dataclass(frozen=True, slots=True)
class Capacity:
    charged_bytes: int
    active_streams: int
    upload_count: int

    @classmethod
    def from_row(cls, row):
        return cls(row["charged_bytes"], row["active_streams"], row["upload_count"])

    def admit(self, limits, added_bytes=0, stream=False, upload=False):
        if (self.charged_bytes + added_bytes > limits.scope_bytes
            or self.active_streams + int(stream) > limits.streams
            or self.upload_count + int(upload) > limits.uploads):
            raise UploadError("capacity_exhausted")
