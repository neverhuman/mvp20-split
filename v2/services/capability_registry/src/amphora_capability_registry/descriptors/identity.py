"""Immutable owner values bind descriptor bytes and every execution/schema pin."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import SchemaRef
from amphora_contracts_tools import LockEntry, PortSchemaLock, ToolBinding


class ReleaseConflict(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReleaseIdentity:
    capability: str
    release: str
    image_sha256: str
    contract_version: str

    @classmethod
    def from_binding(cls, binding):
        return cls(binding.capability_id, binding.release, binding.image_sha256, binding.contract_version)

    @property
    def semantic_key(self):
        return self.capability, self.release, self.contract_version

    def to_binding(self):
        return ToolBinding(capability_id=self.capability, release=self.release,
                           image_sha256=self.image_sha256, contract_version=self.contract_version)


@dataclass(frozen=True, slots=True)
class SchemaIdentity:
    name: str
    version: str
    digest: str

    @classmethod
    def from_ref(cls, ref):
        return cls(ref.schema_id, ref.version, ref.sha256)

    def to_ref(self):
        return SchemaRef(schema_id=self.name, version=self.version, sha256=self.digest)


@dataclass(frozen=True, slots=True)
class PortSchemas:
    inputs: tuple
    outputs: tuple
    checkpoint: SchemaIdentity | None

    @classmethod
    def from_tool(cls, tool):
        def collect(ports):
            return tuple((port.name, SchemaIdentity.from_ref(port.schema_ref)) for port in ports)
        return cls(collect(tool.inputs), collect(tool.outputs),
                   None if tool.checkpoint_schema is None else SchemaIdentity.from_ref(tool.checkpoint_schema))

    @staticmethod
    def to_ports(ports):
        return tuple(PortSchemaLock(port=name, schema_ref=schema.to_ref()) for name, schema in ports)


@dataclass(frozen=True, slots=True)
class ReleaseDocument:
    identity: ReleaseIdentity
    canonical_bytes: bytes
    digest: str
    schemas: PortSchemas

    @classmethod
    def from_descriptor(cls, descriptor):
        normalized = {"profile": "amphora-tool-release-v1", "descriptor": descriptor.model_dump(mode="json")}
        canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                               allow_nan=False).encode("utf-8")
        return cls(ReleaseIdentity.from_binding(descriptor.tool.binding), canonical,
                   hashlib.sha256(canonical).hexdigest(), PortSchemas.from_tool(descriptor.tool))

    def to_lock(self):
        return LockEntry(tool=self.identity.to_binding(), descriptor_sha256=self.digest,
            input_schemas=self.schemas.to_ports(self.schemas.inputs), output_schemas=self.schemas.to_ports(self.schemas.outputs),
            checkpoint_schema=None if self.schemas.checkpoint is None else self.schemas.checkpoint.to_ref())

    def verify_lock(self, expected):
        if expected != self.to_lock():
            raise ReleaseConflict("release_lock_mismatch")

    def require_identical_registration(self, proposed):
        if self.identity.semantic_key != proposed.identity.semantic_key:
            raise ReleaseConflict("release_identity_mismatch")
        if self.digest != proposed.digest or self.canonical_bytes != proposed.canonical_bytes:
            raise ReleaseConflict("immutable_release_conflict")
