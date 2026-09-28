"""Bounded deterministic affine behavior, independent from execution transport."""

import math
from dataclasses import dataclass

from .payloads import AffineInput, AffineOutput


@dataclass(frozen=True, slots=True)
class AffineTransform:
    scale: float
    offset: float

    def apply(self, values):
        result = tuple(self.scale * value + self.offset for value in values)
        if not all(math.isfinite(value) for value in result):
            raise ValueError("nonfinite_result")
        return result


def compute(payload: bytes) -> bytes:
    request = AffineInput.model_validate_json(payload)
    result = AffineTransform(request.a, request.b).apply(request.values)
    return AffineOutput(values=result).model_dump_json().encode()
