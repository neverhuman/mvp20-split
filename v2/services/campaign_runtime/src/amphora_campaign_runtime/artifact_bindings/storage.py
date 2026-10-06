"""Run-locked conversion records and immutable terminal evidence; no peer I/O."""

import json
from datetime import timedelta

from sqlalchemy import text

from ..compiler.catalog import canonical
from ..coordinator.state import persist_node
from ..lifecycle.claims import RUN, SCOPE
from .effective import resolve_effective
from .model import BindingAddress


def load(conn, params):
    return conn.execute(text("SELECT * FROM runtime.binding_intents WHERE " + SCOPE + " AND intent_id=:intent"),
                        params).mappings().one()


def close(conn, params, row, revision, reason=None, outputs=None, resources=None):
    if row["status"] != "prepared":
        return False
    receipt_id = row["intent_id"] + ":closed"
    proof = {"status": "aborted" if reason else "committed", "runtime_receipt_id": receipt_id}
    if reason:
        proof["reason_code"] = reason
    values = {**params, "intent": row["intent_id"], "proof": json.dumps(proof), "status": proof["status"],
        "outputs": None if outputs is None else json.dumps(outputs.record()), "resources": json.dumps(resources),
        "receipt": receipt_id, "revision": revision}
    conn.execute(text("UPDATE runtime.binding_intents SET status=:status,outcome=CAST(:proof AS jsonb),"
        "outputs=CAST(:outputs AS jsonb),resources=CAST(:resources AS jsonb),lease_token=NULL,lease_until=NULL WHERE " +
        SCOPE + " AND intent_id=:intent"), values)
    conn.execute(text("INSERT INTO runtime.binding_closures (tenant_id,project_id,run_id,intent_id,receipt_id,revision,document) "
        "VALUES (:tenant,:project,:run,:intent,:receipt,:revision,CAST(:proof AS jsonb))"), values)
    return True


def stop_bindings(conn, params, run, reason):
    rows = conn.execute(text("SELECT * FROM runtime.binding_intents WHERE " + RUN + " AND status='prepared' ORDER BY intent_id"),
                        params).mappings().all()
    for row in rows:
        close(conn, params, row, run["revision"] + 1, reason)
    return tuple(row["intent_id"] for row in rows)


class BindingExecution:
    def __init__(self, conn, params, plan, graph, run):
        self.conn, self.params, self.plan, self.graph, self.run = conn, params, plan, graph, run
        self.terminal_intents = []

    def step(self, scope, row, node):
        now = self.conn.execute(text("SELECT clock_timestamp()")).scalar_one()
        address = BindingAddress(self.plan.document.definition.scope, self.params["run"], row["activation_id"], self.plan.sha256)
        params = {**self.params, "intent": address.identity}
        if row["status"] == "ready":
            binding = resolve_effective(self.conn, self.params, row['activation_id'], node, scope.environment)
            self.conn.execute(text("INSERT INTO runtime.binding_intents (tenant_id,project_id,run_id,activation_id,intent_id,"
                "plan_sha256,semantic_sha256,node,inputs,deadline,opened_revision,status) VALUES "
                "(:tenant,:project,:run,:activation,:intent,:plan,:sha,CAST(:node AS jsonb),CAST(:inputs AS jsonb),"
                ":deadline,:revision,'prepared')"), {**params, "activation": row["activation_id"], "plan": self.plan.sha256,
                "sha": binding.sha256, "node": canonical(node.model_dump(mode="json")).decode(),
                "inputs": canonical(binding.values.record()).decode(), "revision": self.run["revision"] + 1,
                "deadline": min(self.graph["deadline"], now + timedelta(seconds=node.limits.timeout_seconds))})
            persist_node(self.conn, self.params, row, "issued", state={**row["state"], "binding_intent": address.identity})
            return True
        intent = load(self.conn, params)
        if intent["status"] == "prepared" and now >= intent["deadline"]:
            close(self.conn, params, intent, self.run["revision"] + 1, "binding_deadline_expired")
            self.terminal_intents.append(address.identity)
            persist_node(self.conn, self.params, row, "blocked", reason="binding_deadline_expired")
            return True
        return False
