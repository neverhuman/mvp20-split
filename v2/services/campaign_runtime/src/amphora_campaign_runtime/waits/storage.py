"""Immutable wait opening and issuer-receipt storage; transition policy is separate."""

from sqlalchemy import text

from ..compiler.catalog import canonical
from ..lifecycle.claims import RUN
from .model import ensure


class WaitRecords:
    @staticmethod
    def open(conn, record, opened_revision):
        value = record.expectation
        params = {"tenant": value.scope.tenant_id, "project": value.scope.project_id,
                  "run": value.run_id, "activation": value.activation_id}
        run = conn.execute(text("SELECT status,revision FROM runtime.runs WHERE " + RUN + " FOR UPDATE"),
                           params).mappings().one_or_none()
        ensure(run is not None, "run_unavailable")
        existing = conn.execute(text("SELECT expectation_sha256,expectation,opened_revision FROM runtime.graph_waits WHERE " +
            RUN + " AND activation_id=:activation"), params).mappings().one_or_none()
        document = value.model_dump(mode="json")
        if existing is not None:
            ensure(existing["expectation_sha256"] == record.sha256 and existing["expectation"] == document
                   and existing["opened_revision"] == opened_revision, "wait_already_pinned")
            return record.sha256
        ensure(run["status"] == "running", "run_not_running")
        ensure(type(opened_revision) is int and opened_revision == run["revision"] + 1, "wait_open_revision")
        graph = conn.execute(text("SELECT plan_sha256,deadline FROM runtime.graph_runs WHERE " + RUN),
                             params).mappings().one_or_none()
        ensure(graph is not None and graph["plan_sha256"] == value.plan_sha256, "wait_plan_mismatch")
        ensure(record.deadline <= graph["deadline"], "wait_deadline_exceeds_run")
        kind = conn.execute(text("SELECT kind FROM runtime.graph_nodes WHERE " + RUN + " AND activation_id=:activation"),
                            params).scalar_one_or_none()
        ensure(kind == "await", "wait_node_required")
        ensure(conn.execute(text("SELECT clock_timestamp() < :deadline"), {"deadline": record.deadline}).scalar_one(),
               "wait_deadline_expired")
        conn.execute(text("INSERT INTO runtime.graph_waits (tenant_id,project_id,run_id,activation_id,wait_revision,"
            "expectation_sha256,expectation,deadline,opened_revision) VALUES (:tenant,:project,:run,:activation,"
            ":wait_revision,:sha,CAST(:expectation AS jsonb),:deadline,:opened_revision)"),
            {**params, "wait_revision": value.wait_revision, "sha": record.sha256,
             "expectation": canonical(document).decode(), "deadline": record.deadline, "opened_revision": opened_revision})
        return record.sha256

    @staticmethod
    def retain_receipt(conn, evidence):
        value = evidence.receipt
        params = {"tenant": value.scope.tenant_id, "project": value.scope.project_id,
                  "issuer": value.issuer_id, "receipt": value.receipt_id,
                  "sha": evidence.sha256, "document": canonical(value.model_dump(mode="json")).decode()}
        conn.execute(text("INSERT INTO runtime.graph_wait_receipts "
            "(tenant_id,project_id,issuer_id,receipt_id,receipt_sha256,document) "
            "VALUES (:tenant,:project,:issuer,:receipt,:sha,CAST(:document AS jsonb)) "
            "ON CONFLICT (tenant_id,project_id,issuer_id,receipt_id) DO NOTHING"), params)
        stored = conn.execute(text("SELECT receipt_sha256,document FROM runtime.graph_wait_receipts "
            "WHERE tenant_id=:tenant AND project_id=:project AND issuer_id=:issuer AND receipt_id=:receipt"),
            params).mappings().one()
        ensure(stored["receipt_sha256"] == evidence.sha256 and stored["document"] == value.model_dump(mode="json"),
               "wait_receipt_identity_conflict")
        return evidence.sha256
