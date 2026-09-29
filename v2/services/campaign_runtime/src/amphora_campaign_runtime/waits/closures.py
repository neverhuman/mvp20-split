"""Exact wait closure and graph projection in the caller's audited owner transaction."""

import json

from amphora_contracts_artifacts import ReservationReceipt
from amphora_contracts_campaigns import ActivationPath, parse_execution_plan
from amphora_contracts_graph_runtime import WaitExpectation
from sqlalchemy import text

from ..compiler.catalog import canonical
from ..completion.artifacts import validate_receipt
from ..lifecycle.claims import RUN
from .model import WaitRecord, ensure
from .retention import WaitRetentionIntent
from .storage import WaitRecords


def load_wait(conn, params):
    raw = conn.execute(text("SELECT expectation FROM runtime.graph_waits WHERE " + RUN +
        " AND activation_id=:activation"), params).scalar_one_or_none()
    ensure(raw is not None, "wait_unavailable")
    return WaitRecord(WaitExpectation.model_validate_json(json.dumps(raw)))


class WaitClosures:
    @staticmethod
    def persist(conn, disposition, revision, *, retention_intent=None):
        expected = disposition.wait.expectation
        params = {"tenant": expected.scope.tenant_id, "project": expected.scope.project_id,
                  "run": expected.run_id, "activation": expected.activation_id}
        run = conn.execute(text("SELECT status,revision FROM runtime.runs WHERE " + RUN + " FOR UPDATE"),
                           params).mappings().one_or_none()
        ensure(run is not None, "run_unavailable")
        closure = disposition.closure(revision)
        existing = conn.execute(text("SELECT document FROM runtime.graph_wait_closures WHERE " + RUN +
            " AND activation_id=:activation"), params).scalar_one_or_none()
        if existing is not None:
            ensure(existing == closure.model_dump(mode="json"), "wait_already_closed")
            return closure
        ensure(run["status"] == "running" or disposition.status == "cancelled", "run_not_running")
        ensure(revision == run["revision"] + 1, "wait_close_revision")
        pinned = load_wait(conn, params)
        ensure(pinned.sha256 == disposition.wait.sha256, "wait_expectation_mismatch")
        if disposition.evidence is None and disposition.status != "cancelled":
            ensure(conn.execute(text("SELECT clock_timestamp() >= :deadline"),
                                {"deadline": pinned.deadline}).scalar_one(), "wait_timeout_not_due")
        if disposition.evidence is not None:
            ensure(conn.execute(text("SELECT clock_timestamp() < :deadline"),
                                {"deadline": pinned.deadline}).scalar_one(), "wait_deadline_expired")
            WaitRecords.retain_receipt(conn, disposition.evidence)
        row = conn.execute(text("SELECT path,state FROM runtime.graph_nodes WHERE " + RUN +
                                " AND activation_id=:activation"), params).mappings().one()
        outputs = None
        if disposition.output is not None:
            ensure(retention_intent is not None, "wait_retention_required")
            intent = conn.execute(text("SELECT * FROM runtime.wait_retention_intents WHERE " + RUN +
                " AND activation_id=:activation AND intent_id=:intent"),
                {**params, "intent": retention_intent}).mappings().one_or_none()
            ensure(intent is not None and intent["status"] == "committed"
                   and intent["receipt_sha256"] == disposition.evidence.sha256
                   and intent["expectation_sha256"] == pinned.sha256, "wait_retention_uncommitted")
            saved = conn.execute(text("SELECT receipt FROM runtime.wait_intent_reservations WHERE tenant_id=:tenant "
                "AND project_id=:project AND intent_id=:intent AND output_binding='result'"),
                {**params, "intent": retention_intent}).scalar_one_or_none()
            ensure(saved is not None, "wait_reservation_missing")
            receipt = ReservationReceipt.model_validate_json(json.dumps(saved))
            expected_intent = WaitRetentionIntent(pinned, disposition.evidence, intent["operation_id"],
                                                  receipt.outcome.binding.intent.runtime_owner)
            ensure(expected_intent.intent_id == retention_intent and expected_intent.semantic_sha256 == intent["semantic_sha256"],
                   "wait_retention_identity_mismatch")
            validate_receipt(expected_intent.reservation, receipt)
            raw = conn.execute(text("SELECT document FROM runtime.graph_plans WHERE tenant_id=:tenant "
                "AND project_id=:project AND plan_sha256=:plan"), {**params, "plan": expected.plan_sha256}).scalar_one()
            plan = parse_execution_plan(json.dumps(raw))
            path = ActivationPath.model_validate_json(json.dumps(row["path"]))
            body = plan.document.definition.body
            for occurrence in path.occurrences:
                body = next(node.body for node in body.nodes if node.node_id == occurrence.node_id)
            node = next(node for node in body.nodes if node.node_id == path.node_id)
            outputs = [{"port": node.output.name, "value": disposition.output.model_dump(mode="json")}]
        conn.execute(text("INSERT INTO runtime.graph_wait_closures (tenant_id,project_id,run_id,activation_id,"
            "wait_revision,expectation_sha256,closure_revision,receipt_sha256,document) VALUES "
            "(:tenant,:project,:run,:activation,:wait,:expectation,:revision,:receipt,CAST(:document AS jsonb))"),
            {**params, "wait": expected.wait_revision, "expectation": pinned.sha256, "revision": revision,
             "receipt": None if disposition.evidence is None else disposition.evidence.sha256,
             "document": closure.model_dump_json()})
        conn.execute(text("UPDATE runtime.graph_nodes SET status=:status,reason_code=:reason,outputs=CAST(:outputs AS jsonb),"
            "state=CAST(:state AS jsonb) WHERE " + RUN + " AND activation_id=:activation"),
            {**params, "status": disposition.node_status, "reason": disposition.reason_code,
             "outputs": None if outputs is None else canonical(outputs).decode(),
             "state": canonical({**row["state"], "wait_outcome": closure.outcome.model_dump(mode="json")}).decode()})
        return closure
