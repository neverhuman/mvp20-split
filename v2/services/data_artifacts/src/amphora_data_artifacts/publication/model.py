"""Upload identity, capacity and content policy values."""

import hashlib
from dataclasses import dataclass
from typing import Protocol

from amphora_contracts_artifacts import ContentDescriptor
from amphora_contracts_core import Scope

from .schemas import json_value


class ContentRule(Protocol):
    @property
    def identity(self) -> tuple[str, str, str, str]: ...

    def validate(self, value) -> None: ...


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
    rules: tuple[ContentRule, ...] = ()

    # Narrow registered fixture schemas; arbitrary schema IDs/hashes do not install validators.
    SCHEMAS = {
        "application/octet-stream": b'{"type":"string","contentEncoding":"base64"}',
        "text/plain": b'{"type":"string"}',
        "application/json": b'{"type":"object"}',
    }

    def __post_init__(self):
        identities = [rule.identity for rule in self.rules]
        if len(set(identities)) != len(identities) or set(identities) - self.allowed:
            raise ValueError("Duplicate or unregistered schema validator")
        for media, _identifier, version, digest in self.allowed:
            if (media, _identifier, version, digest) in identities:
                continue
            if (media not in self.SCHEMAS or version != "1"
                or hashlib.sha256(self.SCHEMAS[media]).hexdigest() != digest):
                raise ValueError("Explicit schema validator required")

    def admit(self, descriptor: ContentDescriptor, limits: UploadLimits):
        schema = descriptor.schema_ref
        if (descriptor.media_type, schema.schema_id, schema.version, schema.sha256) not in self.allowed:
            raise UploadError("unsupported_content")
        if descriptor.size_bytes > limits.max_bytes:
            raise UploadError("upload_too_large")

    def validate(self, descriptor, payload):
        """Exact admitted schema identity plus its actual bounded content validator."""
        schema = descriptor.schema_ref
        identity = (descriptor.media_type, schema.schema_id, schema.version, schema.sha256)
        if identity not in self.allowed:
            raise UploadError("unsupported_content")
        if descriptor.media_type == "application/octet-stream":
            return
        try:
            value = payload.decode("utf-8")
            if descriptor.media_type == "application/json":
                value = json_value(payload)
                rule = next((rule for rule in self.rules if rule.identity == identity), None)
                if rule is not None:
                    rule.validate(value)
                elif not isinstance(value, dict):
                    raise ValueError("Object required")
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
