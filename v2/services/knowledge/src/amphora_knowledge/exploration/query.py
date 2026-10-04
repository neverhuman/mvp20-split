"""Complete query pins and bounded continuation; positions confer no access."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_knowledge import (
    GraphEntitySearchRequest,
    GraphNeighborhoodRequest,
    GraphViewPosition,
)

from .index import require


@dataclass(frozen=True, slots=True)
class ExploreQuery:
    request: GraphEntitySearchRequest | GraphNeighborhoodRequest
    sha256: str

    @classmethod
    def prepare(cls, request, revision):
        require(
            type(request) in {GraphEntitySearchRequest, GraphNeighborhoodRequest},
            "query_required",
        )
        request = type(request).model_validate_json(request.model_dump_json())
        require(request.revision == revision, "query_revision")
        search = isinstance(request, GraphEntitySearchRequest)
        if not search:
            require(request.focus.graph == revision.graph, "focus_graph")
        descriptor = {
            "format": "knowledge.explore-query.v1",
            "view": "entity_search" if search else "neighborhood",
            "request": request.model_dump(mode="json", exclude={"position"}),
        }
        raw = json.dumps(
            descriptor,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        result = cls(request, hashlib.sha256(raw).hexdigest())
        if request.position is not None:
            require(request.position.query_sha256 == result.sha256, "position_query")
            if search:
                require(request.position.assertion_offset == 0, "search_position")
        return result

    def offsets(self, entity_total, assertion_total):
        position = self.request.position
        left, right = (
            (0, 0)
            if position is None
            else (position.entity_offset, position.assertion_offset)
        )
        require(left <= entity_total and right <= assertion_total, "position_bound")
        return left, right

    def next_position(self, entity_end, assertion_end, entity_total, assertion_total):
        if entity_end == entity_total and assertion_end == assertion_total:
            return None
        return GraphViewPosition(
            query_sha256=self.sha256,
            entity_offset=entity_end,
            assertion_offset=assertion_end,
        )
