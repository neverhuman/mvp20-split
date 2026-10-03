"""Strict Qdrant point payloads and finite scored observations."""

import math
import uuid
from dataclasses import dataclass

from amphora_contracts_representations import EncodingProfileRef, RepresentationBindingRef

from ...representations.profiles import VectorSpace
from ...representations.vectors import Float32Vector
from ..projection import ProjectionPoint
from ..validation import require
from .transport import QdrantError


def identifier(value):
    try:
        valid = type(value) is str and str(uuid.UUID(value)) == value
    except ValueError:
        valid = False
    require(valid, "qdrant_point_id")
    return value


def vector(dimensions, values):
    space = VectorSpace(dimensions, "float32-le", "none", "dot")
    return Float32Vector.from_values(space, values).values


def encode(point, dimensions):
    require(type(point) is ProjectionPoint, "qdrant_point_required")
    require(point.profile.scope == point.binding.scope, "qdrant_point_scope")
    return {
        "id": identifier(point.point_id),
        "vector": list(vector(dimensions, point.values)),
        "payload": {
            "format": "data.index-point.v1",
            "profile": point.profile.model_dump(mode="json"),
            "binding": point.binding.model_dump(mode="json"),
        },
    }


def decode(value, dimensions):
    try:
        if type(value) is not dict or type(value["payload"]) is not dict or type(value["vector"]) is not list:
            raise QdrantError("qdrant_point_shape")
        payload = value["payload"]
        if set(payload) != {"format", "profile", "binding"} or payload["format"] != "data.index-point.v1":
            raise QdrantError("qdrant_point_payload")
        profile = EncodingProfileRef.model_validate(payload["profile"])
        binding = RepresentationBindingRef.model_validate(payload["binding"])
        require(profile.scope == binding.scope, "qdrant_point_scope")
        return ProjectionPoint(
            identifier(value["id"]), profile, binding, vector(dimensions, tuple(value["vector"]))
        )
    except (ValueError, TypeError, KeyError, OverflowError) as error:
        raise QdrantError("qdrant_point_shape") from error


@dataclass(frozen=True, slots=True)
class ScoredPoint:
    point: ProjectionPoint
    score: float

    def __post_init__(self):
        require(type(self.point) is ProjectionPoint, "qdrant_point_required")
        try:
            valid = type(self.score) in (int, float) and math.isfinite(float(self.score))
        except OverflowError:
            valid = False
        require(valid, "qdrant_score_required")
        object.__setattr__(self, "score", float(self.score))
