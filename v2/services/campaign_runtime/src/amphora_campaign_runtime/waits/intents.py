"""Wait protection tombstones and canonical command settlement; no worker attempts."""

import json

from amphora_contracts_graph_runtime import parse_graph_command
from sqlalchemy import text

from ..lifecycle.claims import RUN, SCOPE
from ..lifecycle.intents import AbortDecision
from ..lifecycle.receipts import RuntimeReply
from .model import ensure


class WaitIntents:
    def __init__(self, leases):
        self.leases = leases

    def abort(self, conn, params, reason, *, activation=None, operation=None, keep=None):
        where = RUN + " AND status='prepared'"
        if activation is not None:
            where += " AND activation_id=:activation"
        if operation is not None:
            where += " AND operation_id=:operation"
        values = {**params, "activation": activation, "operation": operation}
        rows = conn.execute(text("SELECT * FROM runtime.wait_retention_intents WHERE " + where +
                                 " ORDER BY intent_id FOR UPDATE"), values).mappings().all()
        aborted = []
        for row in rows:
            if row["intent_id"] == keep:
                continue
            registered = conn.execute(text("SELECT family,status,canonical_bytes FROM runtime.commands WHERE " + SCOPE +
                " AND operation_id=:operation"), {**params, "operation": row["operation_id"]}).mappings().one()
            ensure(registered["family"] == "graph.submit_receipt" and registered["status"] == "pending",
                   "wait_intent_command_invariant")
            command = parse_graph_command("graph.submit_receipt", bytes(registered["canonical_bytes"]))
            proof = AbortDecision(row["operation_id"], reason).record()
            conn.execute(text("UPDATE runtime.wait_retention_intents SET status='aborted',outcome=CAST(:proof AS jsonb) "
                "WHERE " + SCOPE + " AND intent_id=:intent"),
                {**params, "intent": row["intent_id"], "proof": json.dumps(proof)})
            self.leases._finish(conn, command, RuntimeReply(command, row["operation_id"]).reject(reason))
            aborted.append(row["intent_id"])
        return tuple(aborted)
