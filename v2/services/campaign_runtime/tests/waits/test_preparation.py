"""Wait retention uses stable public artifact bindings, never worker attempt rows."""

import json
import time
import uuid
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.persistence.commands import CommandStore
from amphora_campaign_runtime.waits import WaitPreparation, WaitRecords, WaitRetentionIntent
from amphora_contracts_graph_runtime import parse_graph_command
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .conftest import audit


def prepare_fixture(f, *, change=None):
    with f.env.engine.begin() as conn:
        WaitRecords.open(conn, f.record, 1)
        audit(conn, f, 1)
    expected = f.record.expectation
    payload = {"run_id": expected.run_id, "activation_id": expected.activation_id,
               "wait_revision": expected.wait_revision, "expectation_sha256": f.record.sha256,
               "receipt": f.evidence.receipt.model_dump(mode="json")}
    if change:
        payload.update(change)
    command = parse_graph_command("graph.submit_receipt", json.dumps({"identity": {
        "scope": expected.scope.model_dump(mode="json"), "actor_id": expected.issuer_id,
        "command_family": "graph.submit_receipt", "command_id": uuid.uuid4().hex}, "payload": payload}))
    operation = CommandStore(f.env.engine).register(command).operation_id
    return WaitRetentionIntent(f.record, f.evidence, operation, "runtime-owner")


def test_prepared_protection_identity_is_stable_without_worker_attempt_or_budget(wait_env):
    f = wait_env
    intent = prepare_fixture(f)
    with f.env.engine.begin() as conn:
        row = WaitPreparation.prepare(conn, intent)
    assert row["status"] == "prepared" and row["outcome"] is None
    assert row["output_bindings"] == [intent.reservation.model_dump(mode="json")]
    assert row["semantic_sha256"] == intent.semantic_sha256 and row["intent_id"].startswith("wait:")
    assert intent.reservation.intent.semantic_completion_sha256 == intent.semantic_sha256
    with f.env.engine.begin() as conn:
        assert WaitPreparation.prepare(conn, intent) == row
        assert conn.execute(text("SELECT count(*) FROM runtime.attempts WHERE run_id=:run"), f.params).scalar_one() == 0
        run = conn.execute(text("SELECT reserved,spent,revision FROM runtime.runs WHERE run_id=:run"), f.params).one()
        assert tuple(run) == (0, 0, 1)
        with pytest.raises(TransitionError, match="wait_intent_identity_conflict"):
            WaitPreparation.prepare(conn, replace(intent, runtime_owner="other-owner"))


def test_preparation_must_match_exact_registered_payload(wait_env):
    f = wait_env
    intent = prepare_fixture(f, change={"expectation_sha256": "e" * 64})
    with f.env.engine.begin() as conn:
        with pytest.raises(TransitionError, match="wait_intent_command_mismatch"):
            WaitPreparation.prepare(conn, intent)


def test_missing_command_or_wait_cannot_acquire_protection(wait_env):
    f = wait_env
    intent = WaitRetentionIntent(f.record, f.evidence, "missing-command", "runtime-owner")
    with f.env.engine.begin() as conn:
        with pytest.raises(TransitionError, match="wait_expectation_mismatch"):
            WaitPreparation.prepare(conn, intent)
        WaitRecords.open(conn, f.record, 1)
        audit(conn, f, 1)
        with pytest.raises(TransitionError, match="wait_intent_command_unavailable"):
            WaitPreparation.prepare(conn, intent)


def test_cancelled_run_does_not_replay_prepared_authority_but_preserves_terminal_proof(wait_env):
    f = wait_env
    intent = prepare_fixture(f)
    with f.env.engine.begin() as conn:
        WaitPreparation.prepare(conn, intent)
        conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE run_id=:run"), f.params)
    with f.env.engine.begin() as conn:
        with pytest.raises(TransitionError, match="run_not_running"):
            WaitPreparation.prepare(conn, intent)
        proof = {"status": "aborted", "runtime_receipt_id": intent.operation_id, "reason_code": "run_cancelled"}
        conn.execute(text("UPDATE runtime.wait_retention_intents SET status='aborted',outcome=CAST(:proof AS jsonb) "
            "WHERE run_id=:run AND intent_id=:intent"), {**f.params, "intent": intent.intent_id, "proof": json.dumps(proof)})
        assert WaitPreparation.prepare(conn, intent)["outcome"] == proof


@pytest.mark.parametrize("wait_env", [1], indirect=True)
def test_expired_prepared_intent_does_not_refresh_the_wait_deadline(wait_env):
    f = wait_env
    intent = prepare_fixture(f)
    with f.env.engine.begin() as conn:
        WaitPreparation.prepare(conn, intent)
    time.sleep(max(0, (f.record.deadline - datetime.now(UTC)).total_seconds()) + 0.05)
    with f.env.engine.begin() as conn:
        with pytest.raises(TransitionError, match="wait_deadline_expired"):
            WaitPreparation.prepare(conn, intent)


def test_retention_identity_columns_and_required_terminal_proof_are_enforced(wait_env):
    f = wait_env
    intent = prepare_fixture(f)
    with f.env.engine.begin() as conn:
        WaitPreparation.prepare(conn, intent)
    for sql in ("UPDATE runtime.wait_retention_intents SET semantic_sha256=:sha WHERE run_id=:run",
                "UPDATE runtime.wait_retention_intents SET status='committed' WHERE run_id=:run"):
        with pytest.raises(DBAPIError):
            with f.env.engine.begin() as conn:
                conn.execute(text(sql), {**f.params, "sha": "f" * 64})
