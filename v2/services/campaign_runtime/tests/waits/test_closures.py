"""Real owner closure/audit atomicity and mandatory artifact protection."""

import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.completion.retention import IntentOutcomes, queue_terminal
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.waits import WaitPreparation, WaitRecords
from amphora_campaign_runtime.waits.closures import WaitClosures
from amphora_campaign_runtime.waits.disposition import WaitDisposition
from amphora_contracts_artifacts import ReservationBinding
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..completion.test_acceptance import Peer
from .conftest import audit
from .test_preparation import prepare_fixture


def store_proof(f, intent, *, saved=True):
    reservation = Peer().reserve(intent.reservation)
    with f.env.engine.begin() as conn:
        WaitPreparation.prepare(conn, intent)
        conn.execute(text("UPDATE runtime.wait_retention_intents SET status='committed',outcome=CAST(:proof AS jsonb) "
            "WHERE run_id=:run"), {**f.params, "proof": json.dumps({"status": "committed", "runtime_receipt_id": intent.operation_id})})
        if saved:
            conn.execute(text("INSERT INTO runtime.wait_intent_reservations "
                "(tenant_id,project_id,intent_id,output_binding,receipt) VALUES "
                "(:tenant,:project,:intent,'result',CAST(:receipt AS jsonb))"),
                {**f.params, "intent": intent.intent_id, "receipt": reservation.model_dump_json()})
    return reservation


def test_accepted_wait_closure_requires_exact_retention_and_atomic_audit(wait_env):
    f = wait_env
    intent = prepare_fixture(f)
    receipt = store_proof(f, intent)
    disposition = WaitDisposition.received(f.record, f.evidence)
    with f.env.engine.begin() as conn:
        closure = WaitClosures.persist(conn, disposition, 2, retention_intent=intent.intent_id)
        audit(conn, f, 2)
        queued = queue_terminal(conn, f.params, (intent.intent_id,))
        assert len(queued) == 1
        assert queue_terminal(conn, f.params, (intent.intent_id,)) == queued
    with f.env.engine.begin() as conn:
        assert WaitClosures.persist(conn, disposition, 2, retention_intent=intent.intent_id) == closure
        with pytest.raises(TransitionError, match="wait_already_closed"):
            WaitClosures.persist(conn, WaitDisposition(f.record, "cancelled", "late"), 3)
        node = conn.execute(text("SELECT status,outputs FROM runtime.graph_nodes WHERE run_id=:run AND kind='await'"), f.params).one()
        assert node.status == "succeeded" and node.outputs[0]["value"] == f.evidence.receipt.outcome.output.model_dump(mode="json")
    principal = replace(f.env.principal, actions=f.env.principal.actions | {"outcome"})
    proof = IntentOutcomes(f.env.engine, intent.runtime_owner).lookup(principal, receipt.outcome.binding)
    assert proof.proof.status == "committed" and proof.proof.runtime_receipt_id == intent.operation_id


@pytest.mark.parametrize("case,reason", [("absent", "wait_retention_required"), ("unknown", "wait_retention_uncommitted"),
                                       ("unsaved", "wait_reservation_missing")])
def test_unprotected_wait_never_publishes_output(wait_env, case, reason):
    f = wait_env
    intent = prepare_fixture(f)
    if case == "unsaved":
        store_proof(f, intent, saved=False)
    with f.env.engine.begin() as conn:
        with pytest.raises(TransitionError, match=reason):
            WaitClosures.persist(conn, WaitDisposition.received(f.record, f.evidence), 2,
                                 retention_intent=None if case == "absent" else intent.intent_id)
        assert conn.execute(text("SELECT count(*) FROM runtime.graph_wait_closures WHERE run_id=:run"), f.params).scalar_one() == 0


def test_closure_without_audit_rolls_back_output(wait_env):
    f = wait_env
    with f.env.engine.begin() as conn:
        WaitRecords.open(conn, f.record, 1)
        audit(conn, f, 1)
    with pytest.raises(DBAPIError):
        with f.env.engine.begin() as conn:
            WaitClosures.persist(conn, WaitDisposition(f.record, "cancelled", "cancelled"), 2)
    with f.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.graph_wait_closures WHERE run_id=:run"), f.params).scalar_one() == 0
        assert conn.execute(text("SELECT status FROM runtime.graph_nodes WHERE run_id=:run AND kind='await'"), f.params).scalar_one() == "ready"


def test_storage_rechecks_database_clock_for_timeout(wait_env):
    f = wait_env
    with f.env.engine.begin() as conn:
        WaitRecords.open(conn, f.record, 1)
        audit(conn, f, 1)
    with f.env.engine.begin() as conn:
        with pytest.raises(TransitionError, match="wait_timeout_not_due"):
            WaitClosures.persist(conn, WaitDisposition.timeout(f.record, f.record.deadline), 2)


def test_exact_wait_binding_proves_prepared_and_lost_reply_abort(wait_env):
    f = wait_env
    intent = prepare_fixture(f)
    principal = replace(f.env.principal, actions=f.env.principal.actions | {"outcome"})
    outcomes = IntentOutcomes(f.env.engine, intent.runtime_owner)
    binding = ReservationBinding.model_validate({"reservation_id": "lost-reserve", **intent.reservation.model_dump(mode="json")})
    assert outcomes.lookup(principal, binding).proof.status == "unknown"
    with f.env.engine.begin() as conn:
        WaitPreparation.prepare(conn, intent)
    assert outcomes.lookup(principal, binding).proof.status == "prepared"
    with f.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.wait_retention_intents SET status='aborted',outcome=CAST(:proof AS jsonb) WHERE run_id=:run"),
            {**f.params, "proof": json.dumps({"status": "aborted", "runtime_receipt_id": intent.operation_id, "reason_code": "timeout"})})
    assert outcomes.lookup(principal, binding).proof.status == "aborted"
    changed = binding.model_copy(update={"intent": binding.intent.model_copy(update={"semantic_completion_sha256": "f" * 64})})
    assert outcomes.lookup(principal, changed).proof.status == "unknown"
