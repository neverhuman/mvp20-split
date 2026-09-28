"""Bounded stale PREPARED-intent abort; timeout never fabricates a commit."""

import json
import uuid

from amphora_contracts_runtime import parse_command
from sqlalchemy import text

from ..lifecycle.authority import lock_work
from ..lifecycle.claims import RUN, RuntimeLeases
from ..lifecycle.intents import AbortDecision
from ..lifecycle.model import RunBudget, TransitionError
from ..lifecycle.receipts import RuntimeReply
from .retention import queue_terminal


class StaleIntents:
    def __init__(self, engine):
        self.leases = RuntimeLeases(engine)

    def sweep(self, principal, run_id, *, after="", limit=100):
        principal.require("maintain")
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError("Invalid intent sweep bound")
        params = {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id, "run": run_id,
                  "after": after, "limit": limit}
        def transaction(conn):
            run = self.leases._run(conn, params)
            lock_work(conn, params)
            intents = conn.execute(text("SELECT i.* FROM runtime.completion_intents i JOIN runtime.commands c "
                "ON (c.tenant_id,c.project_id,c.operation_id)=(i.tenant_id,i.project_id,i.operation_id) "
                "WHERE i.tenant_id=:tenant AND i.project_id=:project AND i.run_id=:run "
                "AND (i.status='prepared' OR (i.status='aborted' AND c.status='pending')) "
                "AND i.intent_id>:after ORDER BY i.intent_id LIMIT :limit FOR UPDATE OF i"), params).mappings().all()
            aborted, settled = [], []
            for intent in intents:
                row = conn.execute(text("SELECT a.*,v.current_fence,p.revoked FROM runtime.attempts a "
                    "JOIN runtime.activations v USING (tenant_id,project_id,run_id,activation_id) "
                    "JOIN runtime.worker_policy p USING (tenant_id,project_id,worker_id) "
                    "WHERE a.tenant_id=:tenant AND a.project_id=:project AND a.run_id=:run AND a.attempt_id=:attempt"),
                    {**params, "attempt": intent["attempt_id"]}).mappings().one()
                now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
                reason = (intent["outcome"]["reason_code"] if intent["status"] == "aborted" else
                          "run_not_running" if run["status"] != "running" else
                          "worker_revoked" if row["revoked"] else
                          "stale_attempt" if row["current_fence"] != intent["fence"] else
                          "attempt_not_leased" if row["status"] != "leased" else
                          "lease_expired" if now >= row["lease_expires_at"] or now >= row["deadline"] else None)
                if reason is None:
                    continue
                raw = conn.execute(text("SELECT canonical_bytes,family,status FROM runtime.commands WHERE "
                    "tenant_id=:tenant AND project_id=:project AND operation_id=:operation"),
                    {**params, "operation": intent["operation_id"]}).mappings().one()
                if raw["family"] != "runtime.complete" or raw["status"] != "pending":
                    raise TransitionError("intent_command_invariant")
                command = parse_command("runtime.complete", bytes(raw["canonical_bytes"]))
                if intent["status"] == "prepared":
                    proof = AbortDecision(intent["operation_id"], reason).record()
                    conn.execute(text("UPDATE runtime.completion_intents SET status='aborted',outcome=CAST(:proof AS jsonb) "
                        "WHERE " + RUN + " AND intent_id=:intent AND status='prepared'"),
                        {**params, "intent": intent["intent_id"], "proof": json.dumps(proof)})
                    aborted.append(intent["intent_id"])
                else:
                    settled.append(intent["intent_id"])
                self.leases._finish(conn, command, RuntimeReply(command, intent["operation_id"]).reject(reason))
            if aborted or settled:
                self.leases._changed(conn, params, run, RunBudget(run["budget_limit"], run["reserved"], run["spent"]),
                    uuid.uuid4().hex, {"kind": "stale_intents_reconciled", "aborted": aborted, "settled_commands": settled})
                queue_terminal(conn, params, (*aborted, *settled))
            return {"inspected": len(intents), "aborted": aborted, "settled_commands": settled,
                    "next_cursor": intents[-1]["intent_id"] if len(intents) == limit else None}
        return self.leases.commands.transact(transaction)
