"""Focused, bounded exact-revision projections; source content stays with Data."""

from amphora_contracts_knowledge import (
    GraphEntitySearchPage,
    GraphEntitySearchRequest,
    GraphExploreCapability,
    GraphExploreCatalog,
    GraphExploreLimits,
    GraphNeighborhoodPage,
    GraphNeighborhoodRequest,
    GraphObjectDetail,
    GraphObjectRequest,
    graph_explore_schema,
)

from ..authoring.canonical import canonical
from .index import SnapshotIndex, entity_key, require
from .query import ExploreQuery

MAX_RESPONSE_BYTES = 1048576


def bounded(record):
    require(len(canonical(record)) <= MAX_RESPONSE_BYTES, "response_bound")
    return record


class GraphExploration:
    def __init__(self, snapshot):
        self.index = SnapshotIndex(snapshot)

    def catalog(self):
        views = tuple(
            GraphExploreCapability(
                view_id=name, version="1", result_schema=graph_explore_schema(name)
            )
            for name in ("entity_search", "neighborhood", "object_detail")
        )
        limits = GraphExploreLimits(
            search_page=50,
            entity_page=64,
            assertion_page=128,
            radius=2,
            response_bytes=MAX_RESPONSE_BYTES,
            source_fetch="separate_data_authority",
        )
        return bounded(
            GraphExploreCatalog(
                wire_version="1",
                owner="knowledge",
                revision=self.index.reference,
                views=views,
                limits=limits,
            )
        )

    def search(self, request):
        require(type(request) is GraphEntitySearchRequest, "search_request")
        query = ExploreQuery.prepare(request, self.index.reference)
        request = query.request
        # Literal matching intentionally performs no case folding, normalization or regex expansion.
        rows = tuple(
            r
            for r in self.index.entities.rows(request.history)
            if (
                request.entity_type is None
                or r.record.entity_type == request.entity_type
            )
            and (
                request.text in r.record.label
                or request.text in r.record.reference.entity_id
            )
        )
        start, _ = query.offsets(len(rows), 0)
        selected = rows[start : start + request.limit]
        return bounded(
            GraphEntitySearchPage(
                wire_version="1",
                request=request,
                query_sha256=query.sha256,
                total=len(rows),
                entities=tuple(r.summary() for r in selected),
                next_position=query.next_position(
                    start + len(selected), 0, len(rows), 0
                ),
            )
        )

    def neighborhood(self, request):
        require(type(request) is GraphNeighborhoodRequest, "neighborhood_request")
        query = ExploreQuery.prepare(request, self.index.reference)
        request = query.request
        focus = self.index.entities.get(request.focus)
        assertions = self.index.assertions.rows(request.history)
        selected = {entity_key(focus.record.reference)}
        for _ in range(request.radius):
            frontier = set(selected)
            for row in assertions:
                left, right = (
                    entity_key(row.record.subject),
                    entity_key(row.record.object),
                )
                if left in frontier or right in frontier:
                    selected.update((left, right))
        entities = tuple(
            self.index.entities.get(self.index.entities.records[key].reference)
            for key in sorted(selected)
        )
        assertions = tuple(
            row
            for row in assertions
            if entity_key(row.record.subject) in selected
            and entity_key(row.record.object) in selected
        )
        left, right = query.offsets(len(entities), len(assertions))
        entity_page = entities[left : left + request.entity_limit]
        assertion_page = assertions[right : right + request.assertion_limit]
        returned = {r.record.reference for r in entity_page}
        endpoints = {
            ref
            for row in assertion_page
            for ref in (row.record.subject, row.record.object)
        }
        endpoints.update(
            r.alias_target for r in entity_page if r.alias_target is not None
        )
        unresolved = tuple(sorted(endpoints - returned, key=entity_key))
        return bounded(
            GraphNeighborhoodPage(
                wire_version="1",
                request=request,
                query_sha256=query.sha256,
                entity_total=len(entities),
                assertion_total=len(assertions),
                entities=tuple(r.summary() for r in entity_page),
                assertions=tuple(r.summary() for r in assertion_page),
                unresolved_entities=unresolved,
                next_position=query.next_position(
                    left + len(entity_page),
                    right + len(assertion_page),
                    len(entities),
                    len(assertions),
                ),
            )
        )

    def detail(self, request):
        require(type(request) is GraphObjectRequest, "object_request")
        request = GraphObjectRequest.model_validate_json(request.model_dump_json())
        require(request.revision == self.index.reference, "query_revision")
        selected = request.selection
        index = (
            self.index.entities if selected.kind == "entity" else self.index.assertions
        )
        record = index.get(selected.reference)
        return bounded(
            GraphObjectDetail(wire_version="1", request=request, detail=record.detail())
        )
