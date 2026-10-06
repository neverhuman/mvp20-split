"""Bounded immutable named inputs retain exact Artifact identity and bytes."""

import re
from dataclasses import dataclass
from hashlib import sha256

from amphora_contracts_core import ArtifactRef
from amphora_tool_protocol import ProtocolError

MAX_BYTES = 262144


@dataclass(frozen=True)
class ResolvedInput:
    port: str
    artifact: ArtifactRef
    data: bytes

    def __post_init__(self):
        checked = ArtifactRef.model_validate_json(self.artifact.model_dump_json())
        object.__setattr__(self, "artifact", checked)
        if (type(self.port) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", self.port) is None
            or type(self.data) is not bytes or len(self.data) > MAX_BYTES
            or len(self.data) != checked.size_bytes or sha256(self.data).hexdigest() != checked.sha256):
            raise ProtocolError("tool_input_content_mismatch")


@dataclass(frozen=True)
class InputBundle:
    inputs: tuple[ResolvedInput, ...]

    def __post_init__(self):
        if (type(self.inputs) is not tuple or not 2 <= len(self.inputs) <= 16
            or not all(type(item) is ResolvedInput for item in self.inputs)
            or len({item.port for item in self.inputs}) != len(self.inputs)
            or sum(len(item.data) for item in self.inputs) > MAX_BYTES):
            raise ProtocolError("tool_input_bundle_invalid")

    def __getitem__(self, port):
        for item in self.inputs:
            if item.port == port:
                return item
        raise ProtocolError("tool_input_port_missing")
