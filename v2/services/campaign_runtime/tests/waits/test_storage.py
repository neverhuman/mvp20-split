"""Actual PostgreSQL wait identity, immutable receipts and closure foreign keys."""

from dataclasses import replace

import pytest
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.waits import ReceiptEvidence, WaitRecords
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .conftest import audit


def test_wait_opens_once_with_exact_replay_and_no_deadline_extension(wait_env):
    f = wait_env
    with f.env.engine.begin() as conn:
        assert WaitRecords.open(conn, f.record, 1) == f.record.sha256
        audit(conn, f, 1)
    with f.env.engine.begin() as conn:
        assert WaitRecords.open(conn, f.record, 1) == f.record.sha256
        changed = replace(f.record, expectation=f.record.expectation.model_copy(update={
            "deadline_us": f.record.expectation.deadline_us + 1}))
        with pytest.raises(TransitionError, match="wait_already_pinned"):
            WaitRecords.open(conn, changed, 1)
        stored = conn.execute(text("SELECT expectation,deadline FROM runtime.graph_waits WHERE run_id=:run"), f.params).mappings().one()
        assert stored["expectation"] == f.record.expectation.model_dump(mode="json")
        assert stored["deadline"] == f.record.deadline


def test_wait_without_opening_audit_cannot_commit(wait_env):
    f = wait_env
    with pytest.raises(DBAPIError):
        with f.env.engine.begin() as conn:
            WaitRecords.open(conn, f.record, 1)
    with f.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.graph_waits WHERE run_id=:run"), f.params).scalar_one() == 0


@pytest.mark.parametrize("case,reason", [("run", "run_unavailable"), ("revision", "wait_open_revision"),
    ("plan", "wait_plan_mismatch"), ("node", "wait_node_required"), ("deadline", "wait_deadline_expired"),
    ("bound", "wait_deadline_exceeds_run"), ("cancelled", "run_not_running")])
def test_open_rejects_stale_or_foreign_authority(wait_env, case, reason):
    f = wait_env
    changes = {"run": {"run_id": "unavailable"}, "plan": {"plan_sha256": "e" * 64},
               "node": {"activation_id": "f" * 64}, "deadline": {"deadline_us": 1},
               "bound": {"deadline_us": f.record.expectation.deadline_us + 1000000000}}
    record = replace(f.record, expectation=f.record.expectation.model_copy(update=changes.get(case, {})))
    with f.env.engine.begin() as conn:
        if case == "cancelled":
            conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE run_id=:run"), f.params)
        with pytest.raises(TransitionError, match=reason):
            WaitRecords.open(conn, record, 2 if case == "revision" else 1)


def test_issuer_receipt_identity_is_immutable_and_exact_replay_is_safe(wait_env):
    f = wait_env
    with f.env.engine.begin() as conn:
        assert WaitRecords.retain_receipt(conn, f.evidence) == f.evidence.sha256
    with f.env.engine.begin() as conn:
        assert WaitRecords.retain_receipt(conn, f.evidence) == f.evidence.sha256
        altered = ReceiptEvidence(f.evidence.receipt.model_copy(update={"revision": "other-revision"}))
        with pytest.raises(TransitionError, match="wait_receipt_identity_conflict"):
            WaitRecords.retain_receipt(conn, altered)


@pytest.mark.parametrize("table", ["graph_waits", "graph_wait_receipts", "graph_wait_closures", "wait_intent_reservations"])
def test_wait_evidence_tables_have_no_service_rewrite_or_delete_grants(wait_env, table):
    with wait_env.env.engine.connect() as conn:
        for action in ("UPDATE", "DELETE"):
            assert conn.execute(text("SELECT has_table_privilege(current_user,:table,:action)"),
                                {"table": "runtime." + table, "action": action}).scalar_one() is False


def test_only_one_closure_and_exact_opening_identity_are_storable(wait_env):
    f = wait_env
    with f.env.engine.begin() as conn:
        WaitRecords.open(conn, f.record, 1)
        audit(conn, f, 1)
    sql = text("INSERT INTO runtime.graph_wait_closures (tenant_id,project_id,run_id,activation_id,wait_revision,"
        "expectation_sha256,closure_revision,document) VALUES (:tenant,:project,:run,:activation,1,:sha,2,'{}')")
    params = {**f.params, "activation": f.record.expectation.activation_id, "sha": f.record.sha256}
    with pytest.raises(DBAPIError):
        with f.env.engine.begin() as conn:
            conn.execute(sql, {**params, "sha": "f" * 64})
            audit(conn, f, 2)
    with pytest.raises(DBAPIError):
        with f.env.engine.begin() as conn:
            conn.execute(sql, params)  # Missing closing audit must roll back.
    with f.env.engine.begin() as conn:
        conn.execute(sql, params)
        audit(conn, f, 2)
    with pytest.raises(DBAPIError):
        with f.env.engine.begin() as conn:
            conn.execute(sql, params)
