"""Canonical finite binary32 vectors; no source rights or scientific interpretation."""

import hashlib
import math
import struct
from dataclasses import dataclass

from .profiles import VectorSpace
from .validation import RepresentationError, require


@dataclass(frozen=True, slots=True)
class Float32Vector:
    space: VectorSpace
    payload: bytes

    def __post_init__(self):
        require(type(self.space) is VectorSpace, "representation_vector_space")
        require(
            type(self.payload) is bytes and len(self.payload) == self.space.dimensions * 4,
            "representation_vector_length",
        )
        values = struct.unpack("<" + str(self.space.dimensions) + "f", self.payload)
        require(all(math.isfinite(value) for value in values), "representation_vector_nonfinite")
        require(
            all(value != 0 or math.copysign(1, value) == 1 for value in values),
            "representation_vector_negative_zero",
        )

    @classmethod
    def from_values(cls, space, values):
        require(type(space) is VectorSpace, "representation_vector_space")
        require(type(values) is tuple and len(values) == space.dimensions, "representation_vector_length")
        encoded = []
        for value in values:
            require(type(value) in (int, float), "representation_vector_number")
            try:
                require(math.isfinite(value), "representation_vector_nonfinite")
                raw = struct.pack("<f", value)
            except (OverflowError, struct.error) as error:
                raise RepresentationError("representation_vector_overflow") from error
            rounded = struct.unpack("<f", raw)[0]
            encoded.append(b"\0\0\0\0" if rounded == 0 else raw)
        return cls(space, b"".join(encoded))

    @property
    def values(self):
        return struct.unpack("<" + str(self.space.dimensions) + "f", self.payload)

    @property
    def sha256(self):
        return hashlib.sha256(self.payload).hexdigest()
