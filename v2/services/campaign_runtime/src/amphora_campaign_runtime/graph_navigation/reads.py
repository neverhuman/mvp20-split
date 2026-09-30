"""Owner-scoped read-only projections over retained plans and occurrence records."""

import json
from dataclasses import dataclass, replace

from amphora_contracts_graph_runtime import (
    GraphScopePage,
    GraphScopeView,
    GraphTopologyPage,
    GraphTopologyQuery,
)
from sqlalchemy import text

from ..graph_inspection.policy import ObservedCut, page_limit, read_transaction, require
from ..lifecycle.claims import RUN
from .topology import ScopeTopology

SCOPES = "s.tenant_id=:tenant AND s.project_id=:project AND s.run_id=:run"
NODES = "n.tenant_id=:tenant AND n.project_id=:project AND n.run_id=:run"
SCOPE_SELECT = ("SELECT s.scope_key,s.definition_path,s.occurrences,s.parent_activation_id,s.status,"
    "(SELECT count(*) FROM runtime.graph_nodes n WHERE " + NODES + " AND n.scope_key=s.scope_key) AS node_count "
    "FROM runtime.graph_scopes s WHERE " + SCOPES)


@dataclass(frozen=True)
class ScopeRecord:
    row: object

    def to_wire(self):
        return GraphScopeView.model_validate_json(json.dumps(dict(self.row)))

    @classmethod
    def load(cls, conn, cut, scope_key):
        row = conn.execute(text(SCOPE_SELECT + " AND s.scope_key=:scope_key"),
                           {**cut.params, "scope_key": scope_key}).mappings().one_or_none()
        require(row is not None, "graph_scope_unavailable")
        return cls(row)


def position(cut, cursors, snapshot_token, cursor, mode, selection):
    snapshot = cut.snapshot_position(cursors, snapshot_token)
    return cut.position(cursors, cursor, mode, filter=selection) if cursor else replace(
        snapshot, mode=mode, filter=selection, after=(0, 0, ""))


def authored_definition(conn, cut, record):
    # Traversal and projection happen inside the owner DB; nested bodies/inputs never leave it.
    query = """WITH RECURSIVE selected_body(value,depth) AS (
      SELECT document#>'{document,definition,body}',0 FROM runtime.graph_plans
       WHERE tenant_id=:tenant AND project_id=:project AND plan_sha256=:plan
      UNION ALL
      SELECT child->'body',selected_body.depth+1 FROM selected_body,
       LATERAL jsonb_array_elements(selected_body.value->'nodes') child
       WHERE selected_body.depth<jsonb_array_length(CAST(:path AS jsonb))
         AND child->>'node_id'=CAST(:path AS jsonb)->>selected_body.depth
    ) SELECT jsonb_build_object('nodes',(SELECT jsonb_agg(jsonb_build_object(
        'node_id',node->>'node_id','kind',node->>'kind')) FROM jsonb_array_elements(value->'nodes') node),
        'edges',value->'edges') AS definition FROM selected_body
      WHERE depth=jsonb_array_length(CAST(:path AS jsonb))"""
    row = conn.execute(text(query), {**cut.params, "plan": cut.row["plan_sha256"],
        "path": json.dumps(record.row["definition_path"])}).mappings().one_or_none()
    require(row is not None)
    return row["definition"]


class GraphNavigation:
    def __init__(self, engine, cursors):
        self.engine, self.cursors = engine, cursors

    def scopes(self, principal, run_id, *, snapshot_token, parent_activation_id=None, cursor=None, limit=50):
        page_limit(limit)
        with read_transaction(self.engine) as conn:
            cut = ObservedCut.load(conn, principal, run_id)
            selection = json.dumps({"parent_activation_id": parent_activation_id}, sort_keys=True)
            page = position(cut, self.cursors, snapshot_token, cursor, "graph-scopes", selection)
            params = {**cut.params, "parent": parent_activation_id, "after": page.after[2], "limit": limit + 1}
            if parent_activation_id is not None:
                require(conn.execute(text("SELECT EXISTS(SELECT 1 FROM runtime.graph_nodes WHERE " + RUN +
                    " AND activation_id=:parent)"), params).scalar_one(), "graph_node_unavailable")
            predicate = " AND s.parent_activation_id IS NOT DISTINCT FROM :parent"
            count = conn.execute(text("SELECT count(*) FROM runtime.graph_scopes s WHERE " + SCOPES + predicate), params).scalar_one()
            rows = conn.execute(text(SCOPE_SELECT + predicate + " AND s.scope_key>:after ORDER BY s.scope_key LIMIT :limit"), params).mappings().all()
            visible = rows[:limit]
            following = self.cursors.encode(page.advance((0, 0, visible[-1]["scope_key"]))) if len(rows) > limit else None
            return GraphScopePage(cut=cut.to_wire(), parent_activation_id=parent_activation_id, scope_count=count,
                                  scopes=tuple(ScopeRecord(row).to_wire() for row in visible), next_cursor=following)

    def topology(self, principal, run_id, scope_key, *, snapshot_token, query=None, cursor=None, limit=50):
        page_limit(limit)
        query = query or GraphTopologyQuery()
        selection = json.dumps({"scope_key": scope_key, "query": query.model_dump(mode="json")}, sort_keys=True)
        with read_transaction(self.engine) as conn:
            cut = ObservedCut.load(conn, principal, run_id)
            page = position(cut, self.cursors, snapshot_token, cursor, "graph-topology", selection)
            record = ScopeRecord.load(conn, cut, scope_key)
            rows = conn.execute(text("SELECT n.activation_id,n.node_id,n.path,n.kind,n.status,n.reason_code,"
                "coalesce(c.total,0) AS child_scope_count FROM runtime.graph_nodes n LEFT JOIN "
                "(SELECT parent_activation_id,count(*) AS total FROM runtime.graph_scopes WHERE " + RUN +
                " GROUP BY parent_activation_id) c ON c.parent_activation_id=n.activation_id WHERE " + NODES +
                " AND n.scope_key=:scope_key"), {**cut.params, "scope_key": scope_key}).mappings().all()
            topology = ScopeTopology.from_authored(rows, authored_definition(conn, cut, record)).neighborhood(query)
            nodes, edges, after = topology.page(page.after[2], limit)
            return GraphTopologyPage(cut=cut.to_wire(), graph_scope=record.to_wire(), query=query,
                node_count=len(topology.nodes), edge_count=len(topology.edges),
                nodes=tuple(node.to_wire() for node in nodes), edges=tuple(edge.to_wire() for edge in edges),
                next_cursor=self.cursors.encode(page.advance((0, 0, after))) if after is not None else None)
