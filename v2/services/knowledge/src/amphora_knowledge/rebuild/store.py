"""Short private transactions; no graph lock is held while replaying history."""

from amphora_contracts_knowledge import AcceptedChangeRef, DomainHead, DomainRevisionRef
from sqlalchemy import text

from ..authoring.canonical import KnowledgeError, canonical
from ..persistence.ledger import KnowledgeLedger, lock_graph
from ..persistence.records import SCOPE, graph_key
from .model import RebuildRequest, RebuildStatus

REBUILD_SCOPE = SCOPE + " AND rebuild_id=:rebuild"


def candidate_head(graph, row):
    return DomainHead(snapshot=DomainRevisionRef(graph=graph, revision=row["revision"], sha256=row["snapshot_sha256"]),
        change=AcceptedChangeRef(graph=graph, change_id=row["change_id"], position=row["revision"], sha256=row["change_sha256"]))


class RebuildStore:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def _status(connection, request):
        row = connection.execute(text("SELECT * FROM knowledge.rebuild_intents WHERE " + REBUILD_SCOPE), request.key).mappings().one_or_none()
        if row is None:
            return None
        request.require_same(row)
        initial = DomainHead.model_validate_json(bytes(row["initial_head"]))
        if initial.snapshot.graph != request.graph or initial.change.graph != request.graph:
            raise KnowledgeError("rebuild_storage_mismatch")
        result = connection.execute(text("SELECT * FROM knowledge.rebuild_results WHERE " + REBUILD_SCOPE), request.key).mappings().one_or_none()
        if result is None:
            return RebuildStatus(request, initial)
        head = None
        if result["outcome"] == "published":
            candidate = connection.execute(text("SELECT * FROM knowledge.rebuild_candidates WHERE " + SCOPE +
                " AND candidate_id=:candidate"), request.key | {"candidate": result["candidate_id"]}).mappings().one()
            head = candidate_head(request.graph, candidate)
            if candidate["attempt"] != result["attempts"]:
                raise KnowledgeError("rebuild_storage_mismatch")
        return RebuildStatus(request, initial, result["outcome"], head, result["attempts"], result["code"])

    def begin(self, principal, graph, rebuild_id):
        request = RebuildRequest.authorized(principal, graph, rebuild_id)
        with self.engine.begin() as connection:
            lock_graph(connection, graph)
            previous = self._status(connection, request)
            if previous is not None:
                return previous
            head = KnowledgeLedger._head(connection, graph)
            if head is None:
                raise KnowledgeError("rebuild_graph_unavailable")
            connection.execute(text("INSERT INTO knowledge.rebuild_intents "
                "(tenant_id,project_id,graph_id,rebuild_id,actor_id,request_sha256,request_bytes,initial_head) "
                "VALUES (:tenant,:project,:graph,:rebuild,:actor,:sha,:body,:head)"), request.key |
                {"actor": request.actor_id, "sha": request.sha256, "body": request.raw, "head": canonical(head)})
            return RebuildStatus(request, head)

    def status(self, principal, graph, rebuild_id):
        principal.require("read_graph", graph.scope)
        key = graph_key(graph) | {"rebuild": rebuild_id}
        with self.engine.connect() as connection:
            actor = connection.execute(text("SELECT actor_id FROM knowledge.rebuild_intents WHERE " + REBUILD_SCOPE), key).scalar_one_or_none()
            if actor is None:
                return None
            return self._status(connection, RebuildRequest(graph, rebuild_id, actor))

    def head(self, request):
        with self.engine.connect() as connection:
            return KnowledgeLedger._head(connection, request.graph)

    def stage(self, candidate):
        with self.engine.begin() as connection:
            connection.execute(text("INSERT INTO knowledge.rebuild_candidates "
                "(tenant_id,project_id,graph_id,rebuild_id,candidate_id,attempt,revision,snapshot_sha256,change_id,change_sha256,canonical_bytes) "
                "VALUES (:tenant,:project,:graph,:rebuild,:candidate,:attempt,:revision,:snapshot_sha,:change,:change_sha,:snapshot_bytes)"), candidate.bindings)

    def publish(self, candidate):
        request = candidate.request
        with self.engine.begin() as connection:
            lock_graph(connection, request.graph)
            status = self._status(connection, request)
            if status.outcome != "pending":
                return status
            if KnowledgeLedger._head(connection, request.graph) != candidate.head:
                return None
            row = connection.execute(text("SELECT * FROM knowledge.rebuild_candidates WHERE " + SCOPE +
                " AND candidate_id=:candidate"), candidate.bindings).mappings().one()
            if (row["rebuild_id"] != request.rebuild_id or row["attempt"] != candidate.attempt
                    or candidate_head(request.graph, row) != candidate.head
                    or bytes(row["canonical_bytes"]) != candidate.snapshot_bytes):
                raise KnowledgeError("rebuild_storage_mismatch")
            connection.execute(text("INSERT INTO knowledge.snapshot_publications "
                "(tenant_id,project_id,graph_id,rebuild_id,candidate_id) VALUES (:tenant,:project,:graph,:rebuild,:candidate) "
                "ON CONFLICT (tenant_id,project_id,graph_id) DO UPDATE SET rebuild_id=EXCLUDED.rebuild_id,candidate_id=EXCLUDED.candidate_id"), candidate.bindings)
            connection.execute(text("INSERT INTO knowledge.rebuild_results "
                "(tenant_id,project_id,graph_id,rebuild_id,outcome,candidate_id,attempts) "
                "VALUES (:tenant,:project,:graph,:rebuild,'published',:candidate,:attempt)"), candidate.bindings)
            return self._status(connection, request)

    def finish(self, request, outcome, attempts, code):
        if outcome not in ("failed", "deferred"):
            raise KnowledgeError("invalid_rebuild_outcome")
        with self.engine.begin() as connection:
            lock_graph(connection, request.graph)
            previous = self._status(connection, request)
            if previous.outcome != "pending":
                return previous
            connection.execute(text("INSERT INTO knowledge.rebuild_results "
                "(tenant_id,project_id,graph_id,rebuild_id,outcome,attempts,code) "
                "VALUES (:tenant,:project,:graph,:rebuild,:outcome,:attempts,:code)"),
                request.key | {"outcome": outcome, "attempts": attempts, "code": code})
            return self._status(connection, request)
