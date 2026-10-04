"""Explicit selected-revision identity and deterministic bounded windows."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_research_views import (
    ObservationSeriesRequest,
    PropertyViewRequest,
    ResearchViewPosition,
    SpecimenViewRequest,
)


class ResearchViewError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise ResearchViewError("view_" + code)


def canonical(record):
    value = record.model_dump(mode="json") if hasattr(record, "model_dump") else record
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def bounded(record):
    require(len(canonical(record)) <= 1048576, "response_limit")
    return record


@dataclass(frozen=True, slots=True)
class ViewQuery:
    request: SpecimenViewRequest | PropertyViewRequest | ObservationSeriesRequest
    sha256: str

    @classmethod
    def prepare(cls, request):
        models = {
            SpecimenViewRequest: "specimens",
            PropertyViewRequest: "properties",
            ObservationSeriesRequest: "observation_series",
        }
        require(type(request) in models, "query_type")
        request = type(request).model_validate_json(request.model_dump_json())
        if isinstance(request, PropertyViewRequest):
            require(
                len(set(request.observations)) == len(request.observations),
                "duplicate_observation",
            )
            require(
                all(
                    ref.scope == request.experiment.scope
                    for ref in request.observations
                ),
                "selection_scope",
            )
        descriptor = {
            "format": "research.view-query.v1",
            "view": models[type(request)],
            "request": request.model_dump(mode="json", exclude={"position"}),
        }
        digest = hashlib.sha256(canonical(descriptor)).hexdigest()
        if request.position is not None:
            require(request.position.query_sha256 == digest, "position_query")
        return cls(request, digest)

    def window(self, total):
        offset = 0 if self.request.position is None else self.request.position.offset
        require(offset <= total, "position_bound")
        return offset, min(offset + self.request.limit, total)

    def next_position(self, end, total):
        return (
            None
            if end == total
            else ResearchViewPosition(query_sha256=self.sha256, offset=end)
        )
