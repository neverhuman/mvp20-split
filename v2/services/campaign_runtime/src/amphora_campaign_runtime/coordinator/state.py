"""A transaction-local view of one persisted scope, never an in-memory authority queue."""

import json
from dataclasses import dataclass

from amphora_contracts_campaigns import ActivationPath
from sqlalchemy import text

from ..lifecycle.claims import RUN
from .bindings import ValueEnvironment
from .frontier import ScopeAddress
from .values import BoundValues

TERMINAL = frozenset({"succeeded", "skipped", "failed", "blocked"})


@dataclass(frozen=True)
class ScopeState:
    plan: object
    record: object
    nodes: dict
    address: ScopeAddress
    body: object

    @classmethod
    def load(cls, conn, params, plan, key):
        binding = {**params, "scope": key}
        record = conn.execute(text("SELECT * FROM runtime.graph_scopes WHERE " + RUN + " AND scope_key=:scope"),
                              binding).mappings().one()
        rows = conn.execute(text("SELECT * FROM runtime.graph_nodes WHERE " + RUN + " AND scope_key=:scope"),
                            binding).mappings().all()
        path = ActivationPath.model_validate_json(json.dumps(rows[0]["path"]))
        address = ScopeAddress(plan.sha256, path.occurrences)
        body = plan.document.definition.body
        for occurrence in address.occurrences:
            body = next(node.body for node in body.nodes if node.node_id == occurrence.node_id)
        return cls(plan, record, {row["node_id"]: row for row in rows}, address, body)

    @property
    def environment(self):
        return ValueEnvironment(BoundValues.from_records(self.record["inputs"]), {
            key: BoundValues.from_records(row["outputs"]) for key, row in self.nodes.items()
            if row["status"] == "succeeded" and row["outputs"] is not None})

    def definition(self, row):
        return next(node for node in self.body.nodes if node.node_id == row["node_id"])

    def readiness(self, node):
        """Joins converge mutually exclusive paths; all other controls are AND dependencies."""
        edges = tuple(edge for edge in self.body.edges if edge.target == node.node_id)
        parents = tuple(self.nodes[edge.source] for edge in edges)
        if any(row["status"] not in TERMINAL for row in parents):
            return "waiting"
        excluded = tuple(row["status"] == "skipped" or (row["kind"] == "branch" and
            row["status"] == "succeeded" and row["state"]["route"] != edge.route)
            for edge, row in zip(edges, parents, strict=True))
        if node.kind == "join":
            return "skipped" if edges and all(excluded) else "ready"
        if any(excluded):
            return "skipped"
        if any(row["status"] in {"failed", "blocked"} for row in parents):
            return "blocked"
        return "ready"


def persist_node(conn, params, row, status, *, state=None, outputs=None, reason=None):
    conn.execute(text("UPDATE runtime.graph_nodes SET status=:status,state=CAST(:state AS jsonb),"
        "outputs=CAST(:outputs AS jsonb),reason_code=:reason WHERE " + RUN + " AND activation_id=:activation"),
        {**params, "activation": row["activation_id"], "status": status,
         "state": json.dumps(row["state"] if state is None else state),
         "outputs": None if outputs is None else json.dumps(outputs.record()), "reason": reason})


def persist_scope(conn, params, key, status, outputs=None):
    conn.execute(text("UPDATE runtime.graph_scopes SET status=:status,outputs=CAST(:outputs AS jsonb) WHERE " + RUN +
                      " AND scope_key=:scope"), {**params, "scope": key, "status": status,
        "outputs": None if outputs is None else json.dumps(outputs.record())})
