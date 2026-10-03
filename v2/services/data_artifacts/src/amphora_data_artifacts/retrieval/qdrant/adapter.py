"""Actual pinned Qdrant build/inspect/exact filtered search adapter."""

from ..projection import ProjectionSnapshot
from ..validation import require
from .collections import Collections, dimensions, path, result
from .points import ScoredPoint, decode, encode, identifier, vector
from .transport import QdrantError, QdrantTransport


class QdrantAdapter:
    def __init__(self, configuration):
        self.transport = QdrantTransport(configuration)
        self.collections = Collections(self.transport)
        self.reference = configuration.reference

    def build(self, namespace, snapshot):
        path(namespace)
        require(
            type(snapshot) is ProjectionSnapshot and snapshot.metric == "dot", "qdrant_dot_snapshot_required"
        )
        require(1 <= len(snapshot.points) <= 256, "qdrant_point_bound")
        require(len({p.point_id for p in snapshot.points}) == len(snapshot.points), "qdrant_duplicate_point")
        require(all(p.profile == snapshot.points[0].profile for p in snapshot.points), "qdrant_mixed_profile")
        points = [encode(p, snapshot.dimensions) for p in snapshot.points]
        self.transport.server()
        self.collections.ensure(namespace, snapshot.dimensions)
        for offset in range(0, len(points), 64):
            outcome = result(
                self.transport.request(
                    "PUT", path(namespace) + "/points?wait=true", {"points": points[offset : offset + 64]}
                )
            )
            require(
                type(outcome) is dict and outcome.get("status") == "completed", "qdrant_write_unconfirmed"
            )

    def inspect(self, namespace):
        path(namespace)
        self.transport.server()
        size = dimensions(self.collections.read(namespace))
        observed = result(
            self.transport.request(
                "POST",
                path(namespace) + "/points/scroll",
                {"limit": 257, "with_payload": True, "with_vector": True},
            )
        )
        if type(observed) is not dict or type(observed.get("points")) is not list:
            raise QdrantError("qdrant_scroll_shape")
        require(
            observed.get("next_page_offset") is None and len(observed["points"]) <= 256, "qdrant_corpus_bound"
        )
        points = tuple(decode(value, size) for value in observed["points"])
        require(len({p.point_id for p in points}) == len(points), "qdrant_duplicate_point")
        return ProjectionSnapshot(size, "dot", points)

    def query(self, namespace, values, allowed_ids):
        """Return all exact allowed scores; broker owns current rights, tie order and top-k."""
        path(namespace)
        require(type(allowed_ids) is tuple and len(allowed_ids) <= 256, "qdrant_filter_bound")
        allowed = {identifier(value) for value in allowed_ids}
        require(len(allowed) == len(allowed_ids), "qdrant_duplicate_filter")
        require(type(values) is tuple and 1 <= len(values) <= 4096, "qdrant_query_vector")
        query = vector(len(values), values)
        if not allowed:
            return ()
        self.transport.server()
        size = dimensions(self.collections.read(namespace))
        require(size == len(query), "qdrant_query_dimensions")
        observed = result(
            self.transport.request(
                "POST",
                path(namespace) + "/points/query",
                {
                    "query": list(query),
                    "filter": {"must": [{"has_id": list(allowed_ids)}]},
                    "params": {"exact": True},
                    "limit": len(allowed_ids),
                    "with_payload": True,
                    "with_vector": True,
                },
            )
        )
        if type(observed) is not dict or type(observed.get("points")) is not list:
            raise QdrantError("qdrant_query_shape")
        require(len(observed["points"]) <= len(allowed), "qdrant_query_bound")
        scored, seen = [], set()
        for value in observed["points"]:
            point = decode(value, size)
            require(point.point_id in allowed and point.point_id not in seen, "qdrant_query_filter")
            require("score" in value, "qdrant_score_required")
            scored.append(ScoredPoint(point, value["score"]))
            seen.add(point.point_id)
        require(seen == allowed, "qdrant_query_incomplete")
        return tuple(scored)
