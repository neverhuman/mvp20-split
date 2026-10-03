"""Bounded backend observations and exact owner vector comparison; no success flags."""

import math
import uuid
from dataclasses import dataclass
from typing import Protocol

from amphora_contracts_core import SchemaRef
from amphora_contracts_representations import (
    EncodingProfileRef,
    RepresentationBindingRef,
    RepresentationVector,
)

from ..representations.mapping import _validated, vector_from_wire
from ..representations.vectors import Float32Vector
from .manifest import point_id
from .validation import fingerprint, require


@dataclass(frozen=True, slots=True)
class ProjectionPoint:
    point_id: str
    profile: EncodingProfileRef
    binding: RepresentationBindingRef
    values: tuple[float, ...]

    def __post_init__(self):
        require(
            type(self.point_id) is str and str(uuid.UUID(self.point_id)) == self.point_id,
            "retrieval_point_id",
        )
        _validated(self.profile, EncodingProfileRef)
        _validated(self.binding, RepresentationBindingRef)
        require(type(self.values) is tuple and 1 <= len(self.values) <= 4096, "retrieval_point_bound")
        require(
            all(type(x) in (int, float) and math.isfinite(x) for x in self.values), "retrieval_point_number"
        )

    def descriptor(self, space):
        vector = Float32Vector.from_values(space, self.values)
        return {
            "point_id": self.point_id,
            "profile": self.profile.model_dump(mode="json"),
            "binding": self.binding.model_dump(mode="json"),
            "vector_sha256": vector.sha256,
        }


@dataclass(frozen=True, slots=True)
class ProjectionSnapshot:
    dimensions: int
    metric: str
    points: tuple[ProjectionPoint, ...]

    def __post_init__(self):
        require(
            type(self.dimensions) is int and 1 <= self.dimensions <= 4096, "retrieval_projection_dimensions"
        )
        require(self.metric in {"dot", "cosine", "euclidean"}, "retrieval_projection_metric")
        require(type(self.points) is tuple and len(self.points) <= 257, "retrieval_projection_bound")
        require(all(type(p) is ProjectionPoint for p in self.points), "retrieval_projection_point")


class ProjectionAdapter(Protocol):
    """Trusted adapter must bound I/O, preserve vectors, and inspect actual stored content."""

    @property
    def reference(self) -> SchemaRef: ...

    def build(self, namespace: str, snapshot: ProjectionSnapshot) -> None: ...

    def inspect(self, namespace: str) -> ProjectionSnapshot: ...


def materialize(principal, plan, reads):
    points = []
    for binding in plan.manifest.bindings:
        stored, raw = reads.content(principal, binding.vector.artifact_id)
        require(stored.reference == binding.vector, "retrieval_vector_artifact")
        encoded = vector_from_wire(
            principal.scope, plan.manifest.profile, RepresentationVector.model_validate_json(raw)
        )
        require(encoded.input_sha256 == binding.source.sha256, "retrieval_vector_input")
        points.append(
            ProjectionPoint(point_id(binding), binding.profile, binding.reference, encoded.vector.values)
        )
    space = plan.manifest.profile.space
    return ProjectionSnapshot(space.dimensions, space.metric, tuple(points))


def compare_projection(plan, expected, observed):
    require(type(observed) is ProjectionSnapshot, "retrieval_projection_required")
    require(
        (observed.dimensions, observed.metric) == (expected.dimensions, expected.metric),
        "retrieval_projection_space",
    )
    require(len(observed.points) == len(expected.points), "retrieval_projection_count")
    actual = {p.point_id: p for p in observed.points}
    require(len(actual) == len(observed.points), "retrieval_projection_duplicate")
    space = plan.manifest.profile.space
    descriptors = []
    for point in expected.points:
        other = actual.get(point.point_id)
        require(other is not None, "retrieval_projection_missing")
        expected_value = point.descriptor(space)
        require(other.descriptor(space) == expected_value, "retrieval_projection_content")
        descriptors.append(expected_value)
    return fingerprint(
        {
            "format": "data.index-projection.v1",
            "manifest_sha256": plan.manifest.watermark,
            "dimensions": expected.dimensions,
            "metric": expected.metric,
            "points": descriptors,
        }
    )
