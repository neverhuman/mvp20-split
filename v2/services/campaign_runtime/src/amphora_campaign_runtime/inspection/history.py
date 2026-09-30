"""Read-only scoped receipts/reports and pinned immutable audit membership."""

import json

from amphora_contracts_runtime import AuditPage, CommandReceipt, CompletionRecord, DeliveryPage
from sqlalchemy import text

from ..lifecycle.claims import RUN, SCOPE, decoded
from ..lifecycle.reads import wire_time
from .cursors import InspectionError


class RuntimeHistory:
    def __init__(self, engine, cursors):
        self.engine, self.cursors = engine, cursors

    @staticmethod
    def bindings(principal):
        principal.require("read")
        return {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id}

    def receipt(self, principal, family, command_id, actor_id=None):
        if family in {"definition.save", "definition.validate"}:
            raise InspectionError("command_unavailable")
        params = {**self.bindings(principal), "family": family, "id": command_id,
                  "actor": actor_id or principal.actor_id}
        if params["actor"] != principal.actor_id:
            principal.require("inspect_receipts")
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT status,receipt,request_sha256,operation_id FROM runtime.commands WHERE " + SCOPE +
                " AND actor_id=:actor AND family=:family AND command_id=:id"), params).mappings().one_or_none()
            if row is None:
                raise InspectionError("receipt_unavailable")
            if row["status"] != "pending":
                return decoded(row["receipt"])
            return CommandReceipt.model_validate({"outcome": {"status": "pending", "binding": {
                "identity": {"scope": principal.scope, "actor_id": params["actor"], "command_family": family,
                             "command_id": command_id}, "request_sha256": row["request_sha256"],
                "operation_id": row["operation_id"]}}})

    def completion(self, principal, run_id, completion_id):
        params = {**self.bindings(principal), "run": run_id, "report": completion_id}
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT r.*,c.receipt,EXISTS(SELECT 1 FROM runtime.accepted_completions a "
                "WHERE (a.tenant_id,a.project_id,a.completion_id)=(r.tenant_id,r.project_id,r.report_id)) AS canonical "
                "FROM runtime.attempt_reports r JOIN runtime.commands c ON "
                "(c.tenant_id,c.project_id,c.operation_id)=(r.tenant_id,r.project_id,r.report_id) "
                "WHERE r.tenant_id=:tenant AND r.project_id=:project AND r.run_id=:run AND r.report_id=:report"),
                params).mappings().one_or_none()
            if row is None:
                raise InspectionError("completion_unavailable")
            return CompletionRecord.model_validate_json(json.dumps({"scope": principal.scope.model_dump(), "run_id": run_id,
                "completion_id": completion_id, "activation_id": row["activation_id"], "canonical_result": row["canonical"],
                "retention_reservation_ids": [receipt["outcome"]["binding"]["reservation_id"] for receipt in row["reservations"]],
                "accepted_run_revision": row["receipt"]["outcome"]["committed"]["revision"], "result": row["result"]}))

    def audit(self, principal, run_id, *, limit=50, cursor=None, kind=None, since_revision=None):
        params = {**self.bindings(principal), "run": run_id, "limit": limit + 1}
        if type(limit) is not int or not 1 <= limit <= 100 or (cursor and since_revision is not None):
            raise InspectionError("invalid_page_request")
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn, conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            revision = conn.execute(text("SELECT revision FROM runtime.runs WHERE " + RUN), params).scalar_one_or_none()
            if revision is None:
                raise InspectionError("run_unavailable")
            if since_revision is not None and (type(since_revision) is not int or not 0 <= since_revision <= revision):
                raise InspectionError("snapshot_unavailable")
            position = self.cursors.decode(cursor, mode="audit", scope=principal.scope, resource=run_id, filter=kind) if cursor else self.cursors.start(
                "audit", principal.scope, run_id, revision, (-1, -1, "") if since_revision is None else (since_revision, 2147483647, ""), kind)
            if position.revision > revision:
                raise InspectionError("snapshot_unavailable")
            params.update(snapshot=position.revision, after_revision=position.after[0], after_ordinal=position.after[1], kind=kind)
            predicate = " AND payload->>'kind'=:kind" if kind is not None else ""
            rows = conn.execute(text("SELECT event_id,revision,ordinal,payload->>'kind' AS kind FROM runtime.audit_events WHERE " + RUN +
                " AND revision<=:snapshot AND (revision,ordinal)>(:after_revision,:after_ordinal)" + predicate +
                " ORDER BY revision,ordinal LIMIT :limit"), params).mappings().all()
            page = rows[:limit]
            following = self.cursors.encode(position.advance((page[-1]["revision"], page[-1]["ordinal"], ""))) if len(rows) > limit else None
            return AuditPage.model_validate({"scope": principal.scope, "run_id": run_id, "snapshot_revision": position.revision,
                "entries": tuple({"event_id": row["event_id"], "revision": row["revision"], "ordinal": row["ordinal"],
                                  "event_kind": row["kind"] or "runtime_changed"} for row in page), "next_cursor": following})

    def deliveries(self, principal, journal, event_id, *, limit=50, cursor=None):
        if type(limit) is not int or not 1 <= limit <= 100 or journal not in {"run", "policy"}:
            raise InspectionError("invalid_page_request")
        params = {**self.bindings(principal), "event": event_id, "limit": limit + 1}
        table, audit = ("outbox", "audit_events") if journal == "run" else ("policy_outbox", "policy_audit_events")
        with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn, conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            revision = conn.execute(text(f"SELECT revision FROM runtime.{audit} WHERE " + SCOPE +
                " AND event_id=:event"), params).scalar_one_or_none()
            if revision is None:
                raise InspectionError("event_unavailable")
            position = self.cursors.decode(cursor, mode="deliveries:" + journal, scope=principal.scope, resource=event_id) if cursor else self.cursors.start(
                "deliveries:" + journal, principal.scope, event_id, revision, (0, 0, ""))
            params["after"] = position.after[2]
            rows = conn.execute(text(f"SELECT * FROM runtime.{table} WHERE event_id=:event AND operation_id>:after "
                                     "ORDER BY operation_id LIMIT :limit"), params).mappings().all()
            page = rows[:limit]
            following = self.cursors.encode(position.advance((0, 0, page[-1]["operation_id"]))) if len(rows) > limit else None
            return DeliveryPage.model_validate({"scope": principal.scope, "journal": journal, "event_id": event_id,
                "entries": tuple(delivery_entry(row) for row in page), "next_cursor": following})

    def delivery(self, principal, operation_id):
        params = {**self.bindings(principal), "operation": operation_id}
        with self.engine.connect() as conn:
            for journal, table, audit in (("run", "outbox", "audit_events"), ("policy", "policy_outbox", "policy_audit_events")):
                row = conn.execute(text(f"SELECT o.* FROM runtime.{table} o JOIN runtime.{audit} a USING (event_id) "
                    "WHERE o.operation_id=:operation AND a.tenant_id=:tenant AND a.project_id=:project"), params).mappings().one_or_none()
                if row is not None:
                    return DeliveryPage.model_validate({"scope": principal.scope, "journal": journal,
                        "event_id": row["event_id"], "entries": (delivery_entry(row),), "next_cursor": None})
        raise InspectionError("delivery_unavailable")


def delivery_entry(row):
    return {"operation_id": row["operation_id"], "event_id": row["event_id"], "target": row["target"],
        "status": row["status"], "attempts": row["delivery_attempts"], "generation": row["delivery_generation"],
        "available_at": wire_time(row["available_at"]), "last_reason": row["last_reason"],
        "lease_expires_at": None if row["lease_expires_at"] is None else wire_time(row["lease_expires_at"])}
