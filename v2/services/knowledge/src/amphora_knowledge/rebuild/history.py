"""Read immutable owner log slices, close SQL, then reconstruct in memory."""

from amphora_contracts_knowledge import AcceptedGraphChange
from sqlalchemy import text

from ..authoring.canonical import KnowledgeError
from ..persistence.ledger import MAX_CHANGES, MAX_LOG_BYTES
from ..persistence.records import SCOPE, GraphProfile, graph_key
from ..replay.chain import GraphReplay


class RebuildHistory:
    def __init__(self, engine):
        self.engine = engine

    def cursor(self, graph):
        with self.engine.connect() as connection:
            row = connection.execute(text("SELECT * FROM knowledge.graph_profiles WHERE " + SCOPE), graph_key(graph)).mappings().one()
        profile = GraphProfile.restore(row)
        return GraphReplay(graph, profile.vocabulary, profile.policy).cursor()

    def tail(self, graph, after, watermark):
        if watermark is None or watermark.change.graph != graph or watermark.snapshot.graph != graph:
            raise KnowledgeError("replay_graph_mismatch")
        with self.engine.connect() as connection:
            rows = connection.execute(text("SELECT canonical_bytes FROM knowledge.accepted_changes WHERE " + SCOPE +
                " AND position>:after AND position<=:through ORDER BY position"), graph_key(graph) |
                {"after": after, "through": watermark.change.position}, execution_options={"stream_results": True})
            bodies, size = [], 0
            try:
                for raw, in rows:
                    size += len(raw)
                    if size > MAX_LOG_BYTES or len(bodies) >= MAX_CHANGES:
                        raise KnowledgeError("stored_history_limit")
                    bodies.append(bytes(raw))
            finally:
                rows.close()
        return (AcceptedGraphChange.model_validate_json(raw) for raw in bodies)
