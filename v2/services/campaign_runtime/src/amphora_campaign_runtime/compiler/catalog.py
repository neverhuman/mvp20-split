"""Immutable resolver inputs; verify public byte/lock profiles without peer imports or I/O."""

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType

from amphora_contracts_tools import LockEntry, ReleaseDescriptor

from ..execution_profiles import StructuralExecutionProfile
from .errors import require
from .shapes import ArtifactShape, SchemaIdentity, TypedPort


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()


def binding_key(binding):
    return binding.capability_id, binding.release, binding.contract_version, binding.image_sha256


@dataclass(frozen=True)
class ResolvedTool:
    descriptor: ReleaseDescriptor
    lock: LockEntry
    execution_profile: StructuralExecutionProfile | None = None

    def __post_init__(self):
        descriptor, lock = self.descriptor, self.lock
        document = {"profile": "amphora-tool-release-v1", "descriptor": descriptor.model_dump(mode="json")}
        location = descriptor.tool.binding.capability_id
        require(hashlib.sha256(canonical(document)).hexdigest() == lock.descriptor_sha256,
                "descriptor_digest_mismatch", location)
        require(descriptor.tool.binding == lock.tool, "tool_lock_mismatch", location)
        for name in ("inputs", "outputs"):
            actual = tuple((p.name, p.schema_ref) for p in getattr(descriptor.tool, name))
            expected = tuple((p.port, p.schema_ref) for p in getattr(lock, "input_schemas" if name == "inputs" else "output_schemas"))
            require(actual == expected, "schema_lock_mismatch", location)
            require(len({p[0] for p in actual}) == len(actual), "duplicate_tool_port", location)
        require(descriptor.tool.checkpoint_schema == lock.checkpoint_schema, "checkpoint_lock_mismatch", location)
        if self.execution_profile is None:
            require(descriptor.tool.side_effects == "pure" and descriptor.authority_ceiling == "synthetic_only",
                    "unsupported_compiler_tool_profile", location)
        else:
            require(type(self.execution_profile) is StructuralExecutionProfile, "unsupported_compiler_tool_profile", location)
            self.execution_profile.require_descriptor(descriptor, lock)
        require(all(port.required for port in descriptor.tool.outputs), "unsupported_optional_tool_output", location)

    def ports(self, name):
        return tuple(TypedPort(port.name, ArtifactShape.from_port(port))
                     for port in sorted(getattr(self.descriptor.tool, name), key=lambda value: value.name))

    def schemas(self):
        values = [port.schema_ref for port in (*self.descriptor.tool.inputs, *self.descriptor.tool.outputs)]
        if self.lock.checkpoint_schema:
            values.append(self.lock.checkpoint_schema)
        return tuple(SchemaIdentity.from_wire(value) for value in values)


class ToolCatalog:
    def __init__(self, releases):
        releases = tuple(releases)
        entries = {binding_key(tool.lock.tool): tool for tool in releases}
        require(len(entries) == len(releases), "duplicate_tool_identity", "catalog")
        self._entries = MappingProxyType(entries)

    def require(self, binding, location):
        tool = self._entries.get(binding_key(binding))
        require(tool is not None, "unknown_tool_pin", location)
        return tool
