"""Scoped SKIP LOCKED claims and conditional acknowledgement; no network calls."""

import uuid
from datetime import timedelta

from sqlalchemy import text

from ..persistence.commands import CommandStore
from .model import DeliveryClaim, DeliveryPolicy

JOURNALS = {"outbox": ("audit_events", "run_id"), "policy_outbox": ("policy_audit_events", "worker_id")}


class DeliveryStore:
    def __init__(self, engine, policy=None):
        self.commands = CommandStore(engine)
        self.policy = policy or DeliveryPolicy()

    def claim(self, principal, *, limit=20):
        principal.require("deliver")
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Invalid delivery batch bound")
        params = {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id, "limit": limit}
        def transaction(conn):
            candidates = []
            for journal, (audit, identity) in JOURNALS.items():
                rows = conn.execute(text(f"SELECT o.*,a.{identity} AS object_id,a.revision,a.payload AS event_payload "
                    f"FROM runtime.{journal} o JOIN runtime.{audit} a USING (event_id) "
                    "WHERE a.tenant_id=:tenant AND a.project_id=:project AND "
                    "((o.status='pending' AND o.available_at<=clock_timestamp()) OR "
                    "(o.status='leased' AND o.lease_expires_at<=clock_timestamp())) "
                    "ORDER BY o.created_at,o.operation_id LIMIT :limit FOR UPDATE OF o SKIP LOCKED"), params).mappings().all()
                candidates.extend((journal, row) for row in rows)
            candidates.sort(key=lambda pair: (pair[1]["created_at"], pair[1]["operation_id"]))
            claims = []
            for journal, row in candidates:
                if len(claims) == limit:
                    break
                now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
                if row["delivery_attempts"] >= self.policy.max_attempts:
                    conn.execute(text(f"UPDATE runtime.{journal} SET status='exhausted',delivery_token=NULL,"
                        "lease_expires_at=NULL,last_reason='delivery_attempt_limit' WHERE operation_id=:operation"),
                        {"operation": row["operation_id"]})
                    continue
                token, generation = uuid.uuid4().hex, row["delivery_generation"] + 1
                attempt = row["delivery_attempts"] + 1
                conn.execute(text(f"UPDATE runtime.{journal} SET status='leased',delivery_token=:token,"
                    "delivery_generation=:generation,delivery_attempts=:attempt,lease_expires_at=:expiry,last_reason=NULL "
                    "WHERE operation_id=:operation"), {"operation": row["operation_id"], "token": token,
                        "generation": generation, "attempt": attempt, "expiry": now + timedelta(seconds=self.policy.lease_seconds)})
                claims.append(DeliveryClaim(journal, principal.scope, row["operation_id"], row["event_id"], row["target"],
                    row["payload"], row["object_id"], row["revision"], row["event_payload"].get("kind", "runtime_changed"),
                    token, generation, attempt))
            return tuple(claims)
        return self.commands.transact(transaction)

    def finish(self, principal, claim, *, acknowledged, reason="delivery_failed"):
        principal.require("deliver")
        if claim.scope != principal.scope or claim.journal not in JOURNALS:
            raise ValueError("Delivery scope/journal mismatch")
        journal = claim.journal
        audit = JOURNALS[journal][0]
        params = {"operation": claim.operation_id, "tenant": principal.scope.tenant_id,
                  "project": principal.scope.project_id}
        def transaction(conn):
            row = conn.execute(text(f"SELECT o.* FROM runtime.{journal} o JOIN runtime.{audit} a USING (event_id) "
                "WHERE o.operation_id=:operation AND a.tenant_id=:tenant AND a.project_id=:project FOR UPDATE OF o"),
                params).mappings().one_or_none()
            now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
            if (row is None or row["status"] != "leased" or row["delivery_token"] != claim.token
                or row["delivery_generation"] != claim.generation or now >= row["lease_expires_at"]):
                return False
            status = "acknowledged" if acknowledged else "exhausted" if row["delivery_attempts"] >= self.policy.max_attempts else "pending"
            conn.execute(text(f"UPDATE runtime.{journal} SET status=:status,delivery_token=NULL,lease_expires_at=NULL,"
                "available_at=:available,last_reason=:reason WHERE operation_id=:operation"),
                {**params, "status": status, "available": now + timedelta(seconds=self.policy.backoff(row["delivery_attempts"])),
                 "reason": None if acknowledged else reason})
            return True
        return self.commands.transact(transaction)
