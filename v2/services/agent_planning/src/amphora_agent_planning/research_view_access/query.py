"""Immutable campaign-bound selection of one named Research page."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_research_views import (
    ObservationSeriesPage,
    ObservationSeriesRequest,
    PropertyViewPage,
    PropertyViewRequest,
    SpecimenViewPage,
    SpecimenViewRequest,
)
from pydantic import BaseModel

from ..context import RequestSnapshot
from ..context.policy import require

VIEWS = {
    "specimens": (SpecimenViewRequest, SpecimenViewPage, "/v1/research-explore/specimens"),
    "properties": (PropertyViewRequest, PropertyViewPage, "/v1/research-explore/properties"),
    "observation_series": (ObservationSeriesRequest, ObservationSeriesPage, "/v1/research-explore/observation-series"),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def scoped(value, scope):
    if isinstance(value, Scope):
        require(value == scope, "research_view_scope")
    elif isinstance(value, BaseModel):
        for name in type(value).model_fields:
            scoped(getattr(value, name), scope)
    elif isinstance(value, (tuple, list)):
        for item in value:
            scoped(item, scope)


@dataclass(frozen=True)
class ViewSelection:
    view: str
    canonical: bytes
    request: RequestSnapshot

    @classmethod
    def bind(cls, query, request):
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        require(original.purpose in {"campaign_proposal", "supervision"}, "research_view_purpose")
        names = [name for name, (model, _, _) in VIEWS.items() if type(query) is model]
        require(len(names) == 1, "research_view_query_type")
        query = type(query).model_validate(query.model_dump(mode="python", warnings=False))
        raw = query.model_dump_json(warnings=False).encode("utf-8")
        require(len(raw) <= 262144, "research_view_query_size")
        query = type(query).model_validate_json(raw)
        scoped(query, original.reference.scope)
        if isinstance(query, PropertyViewRequest):
            require(len(set(query.observations)) == len(query.observations), "research_view_duplicate_observation")
        result = cls(names[0], canonical(query.model_dump(mode="json")), request)
        require(query.position is None or query.position.query_sha256 == result.query_sha256,
                "research_view_position")
        return result

    def document(self):
        require(self.view in VIEWS, "research_view_query_type")
        require(type(self.canonical) is bytes and len(self.canonical) <= 262144, "research_view_query_size")
        return VIEWS[self.view][0].model_validate_json(self.canonical)

    @property
    def query_sha256(self):
        descriptor = {"format": "research.view-query.v1", "view": self.view,
                      "request": self.document().model_dump(mode="json", exclude={"position"})}
        return hashlib.sha256(canonical(descriptor)).hexdigest()

    @property
    def sha256(self):
        return hashlib.sha256(canonical({"format": "planning.research-view-selection.v1", "view": self.view,
            "query": self.document().model_dump(mode="json"), "request_sha256": self.request.sha256})).hexdigest()
