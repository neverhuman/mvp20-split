"""Observed release identity, separate from eligibility and compiler review."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_tools import LockEntry, PortSchemaLock, ReleaseSnapshot

from ..context.policy import require


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class ObservedRelease:
    canonical: bytes

    @classmethod
    def bind(cls, supplied, scope, expected=None):
        require(type(supplied) is ReleaseSnapshot, "registry_record_type")
        record = ReleaseSnapshot.model_validate(supplied.model_dump(mode="python", warnings=False))
        require(record.scope == scope, "registry_scope")
        descriptor = record.descriptor
        encoded = canonical({"profile": "amphora-tool-release-v1", "descriptor": descriptor.model_dump(mode="json")})
        require(len(encoded) <= 262144, "registry_descriptor_size")
        tool = descriptor.tool
        for ports in (tool.inputs, tool.outputs):
            require(len({port.name for port in ports}) == len(ports), "registry_duplicate_port")
        lock = LockEntry(tool=tool.binding, descriptor_sha256=hashlib.sha256(encoded).hexdigest(),
            input_schemas=tuple(PortSchemaLock(port=port.name, schema_ref=port.schema_ref) for port in tool.inputs),
            output_schemas=tuple(PortSchemaLock(port=port.name, schema_ref=port.schema_ref) for port in tool.outputs),
            checkpoint_schema=tool.checkpoint_schema)
        require(lock == record.lock and (expected is None or lock == expected), "registry_lock")
        return cls(canonical(record.model_dump(mode="json")))

    def document(self):
        return ReleaseSnapshot.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
