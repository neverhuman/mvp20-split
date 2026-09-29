"""Durable wait retention preparation before any external reservation request."""

import json

from amphora_contracts_graph_runtime import SubmitDomainReceipt, parse_graph_command
from sqlalchemy import text

from ..compiler.catalog import canonical
from ..lifecycle.claims import RUN
from .model import ensure
from .storage import WaitRecords


class WaitPreparation:
    @staticmethod
    def prepare(conn, intent):
        expected = intent.wait.expectation
        params = {"tenant": expected.scope.tenant_id, "project": expected.scope.project_id,
                  "run": expected.run_id, "activation": expected.activation_id,
                  "intent": intent.intent_id, "operation": intent.operation_id}
        run = conn.execute(text("SELECT status FROM runtime.runs WHERE " + RUN + " FOR UPDATE"),
                           params).mappings().one_or_none()
        ensure(run is not None, "run_unavailable")
        bindings = [intent.reservation.model_dump(mode="json")]
        existing = conn.execute(text("SELECT * FROM runtime.wait_retention_intents WHERE tenant_id=:tenant "
            "AND project_id=:project AND operation_id=:operation"), params).mappings().one_or_none()
        if existing is not None:
            ensure(existing["intent_id"] == intent.intent_id and existing["semantic_sha256"] == intent.semantic_sha256
                   and existing["output_bindings"] == bindings, "wait_intent_identity_conflict")
            if existing["status"] != "prepared":
                return dict(existing)
        ensure(run["status"] == "running", "run_not_running")
        wait = conn.execute(text("SELECT * FROM runtime.graph_waits WHERE " + RUN + " AND activation_id=:activation"),
                            params).mappings().one_or_none()
        ensure(wait is not None and wait["expectation_sha256"] == intent.wait.sha256
               and wait["wait_revision"] == expected.wait_revision, "wait_expectation_mismatch")
        ensure(not conn.execute(text("SELECT EXISTS(SELECT 1 FROM runtime.graph_wait_closures WHERE " + RUN +
            " AND activation_id=:activation)"), params).scalar_one(), "wait_already_closed")
        ensure(conn.execute(text("SELECT clock_timestamp() < :deadline"), {"deadline": wait["deadline"]}).scalar_one(),
               "wait_deadline_expired")
        registered = conn.execute(text("SELECT family,status,canonical_bytes FROM runtime.commands WHERE tenant_id=:tenant "
            "AND project_id=:project AND operation_id=:operation"), params).mappings().one_or_none()
        ensure(registered is not None and registered["family"] == "graph.submit_receipt" and registered["status"] == "pending",
               "wait_intent_command_unavailable")
        command = parse_graph_command("graph.submit_receipt", bytes(registered["canonical_bytes"]))
        request = SubmitDomainReceipt.model_validate_json(json.dumps(json.loads(command.canonical_bytes)["payload"]))
        ensure(request.run_id == expected.run_id and request.activation_id == expected.activation_id
               and request.wait_revision == expected.wait_revision and request.expectation_sha256 == intent.wait.sha256
               and request.receipt == intent.evidence.receipt, "wait_intent_command_mismatch")
        if existing is not None:
            return dict(existing)
        WaitRecords.retain_receipt(conn, intent.evidence)
        conn.execute(text("INSERT INTO runtime.wait_retention_intents (tenant_id,project_id,intent_id,run_id,activation_id,"
            "wait_revision,expectation_sha256,operation_id,semantic_sha256,output_bindings,receipt_sha256,status) "
            "VALUES (:tenant,:project,:intent,:run,:activation,:wait_revision,:expectation,:operation,:semantic,"
            "CAST(:bindings AS jsonb),:receipt,'prepared')"),
            {**params, "wait_revision": expected.wait_revision, "expectation": intent.wait.sha256,
             "semantic": intent.semantic_sha256, "bindings": canonical(bindings).decode(), "receipt": intent.evidence.sha256})
        return dict(conn.execute(text("SELECT * FROM runtime.wait_retention_intents WHERE tenant_id=:tenant "
            "AND project_id=:project AND intent_id=:intent"), params).mappings().one())
