"""Scoped bounded graph observations; worker/attempt authority stays in the lifecycle."""

import json
import re
from dataclasses import dataclass

from amphora_contracts_graph_runtime import GraphRunPage
from sqlalchemy import text

from ..lifecycle.claims import RUN
from ..lifecycle.model import RunBudget, integer
from .values import ensure


@dataclass(frozen=True)
class ObservedGraph:
    scope: object
    run: object
    graph: object
    count: int
    rows: tuple
    limit: int

    def to_wire(self):
        budget = RunBudget(self.run["budget_limit"], self.run["reserved"], self.run["spent"])
        visible = self.rows[:self.limit]
        nodes = [{key: row[key] for key in ("activation_id", "path", "kind", "status", "reason_code")} for row in visible]
        return GraphRunPage.model_validate_json(json.dumps({"scope": self.scope.model_dump(mode="json"),
            "run_id": self.run["run_id"], "plan_sha256": self.graph["plan_sha256"], "status": self.run["status"],
            "revision": self.run["revision"], "node_count": self.count, "budget_limit": budget.limit,
            "reserved": budget.reserved, "spent": budget.spent, "stop_reason": self.graph["stop_reason"],
            "nodes": nodes, "next_after": visible[-1]["activation_id"] if len(self.rows) > self.limit else None}))


class GraphReads:
    def __init__(self, engine):
        self.engine = engine

    def run(self, principal, run_id, *, after=None, limit=100):
        principal.require("read")
        integer(limit, 1, 100)
        ensure(after is None or isinstance(after, str) and re.fullmatch(r"[0-9a-f]{64}", after), "invalid_graph_cursor")
        params = {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id, "run": run_id,
                  "after": after or "", "limit": limit + 1}
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn, conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            run = conn.execute(text("SELECT * FROM runtime.runs WHERE " + RUN + " AND execution_mode='graph'"), params).mappings().one_or_none()
            ensure(run is not None, "run_unavailable")
            graph = conn.execute(text("SELECT * FROM runtime.graph_runs WHERE " + RUN), params).mappings().one()
            count = conn.execute(text("SELECT count(*) FROM runtime.graph_nodes WHERE " + RUN), params).scalar_one()
            rows = tuple(conn.execute(text("SELECT activation_id,path,kind,status,reason_code FROM runtime.graph_nodes WHERE " + RUN +
                " AND activation_id>:after ORDER BY activation_id LIMIT :limit"), params).mappings().all())
            return ObservedGraph(principal.scope, run, graph, count, rows, limit).to_wire()
