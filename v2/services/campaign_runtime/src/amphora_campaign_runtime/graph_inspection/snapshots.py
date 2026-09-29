"""Bounded frontier/scope pages never mix mutable node state across revisions."""

from dataclasses import dataclass

from amphora_contracts_graph_runtime import GraphReadQuery, GraphReadSnapshot, GraphSnapshotPage
from sqlalchemy import text

from ..lifecycle.claims import RUN
from .policy import ObservedCut, node_view, page_limit, read_transaction, require


@dataclass(frozen=True)
class SnapshotSelection:
    query: GraphReadQuery

    @property
    def fingerprint(self):
        return self.query.model_dump_json()

    @property
    def predicate(self):
        return (" AND scope_key=:scope_key" if self.query.scope_key is not None else "") + (
            " AND status IN ('waiting','ready','issued')" if self.query.frontier_only else "")

    def require_scope(self, conn, params):
        if self.query.scope_key is not None:
            require(conn.execute(text("SELECT EXISTS(SELECT 1 FROM runtime.graph_scopes WHERE " + RUN +
                " AND scope_key=:scope_key)"), params).scalar_one(), "graph_scope_unavailable")


class GraphSnapshots:
    def __init__(self, engine, cursors):
        self.engine, self.cursors = engine, cursors

    def page(self, principal, run_id, *, query=None, cursor=None, limit=50):
        page_limit(limit)
        selection = SnapshotSelection(query or GraphReadQuery())
        with read_transaction(self.engine) as conn:
            cut = ObservedCut.load(conn, principal, run_id)
            position = cut.position(self.cursors, cursor, "graph-nodes", filter=selection.fingerprint, after=(0, 0, ""))
            params = {**cut.params, "scope_key": selection.query.scope_key, "after": position.after[2], "limit": limit + 1}
            selection.require_scope(conn, params)
            count = conn.execute(text("SELECT count(*) FROM runtime.graph_nodes WHERE " + RUN + selection.predicate), params).scalar_one()
            rows = conn.execute(text("SELECT activation_id,path,kind,status,reason_code FROM runtime.graph_nodes WHERE " + RUN +
                selection.predicate + " AND activation_id>:after ORDER BY activation_id LIMIT :limit"), params).mappings().all()
            visible = rows[:limit]
            next_cursor = self.cursors.encode(position.advance((0, 0, visible[-1]["activation_id"]))) if len(rows) > limit else None
            snapshot_token, event_cursor = cut.tokens(self.cursors, position)
            snapshot = GraphReadSnapshot(cut=cut.to_wire(), status=cut.row["status"], budget=cut.budget(), query=selection.query,
                node_count=count, snapshot_token=snapshot_token, event_cursor=event_cursor)
            return GraphSnapshotPage(snapshot=snapshot, nodes=tuple(node_view(row) for row in visible), next_cursor=next_cursor)
