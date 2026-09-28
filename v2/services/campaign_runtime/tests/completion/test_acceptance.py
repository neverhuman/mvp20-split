"""Atomic result/checkpoint acceptance, independent activations and retry history."""

import copy
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.completion.commit import CompletionCommitter
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.completion.prepare import IntentPreparation
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_contracts_artifacts import ReservationReceipt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text


class Peer:
    owner = "runtime"

    def reserve(self, reservation):
        return ReservationReceipt.model_validate({"outcome": {"status": "reserved", "binding": {
            "reservation_id": "r-" + reservation.intent.intent_id + "-" + reservation.intent.output_binding,
            "artifact": reservation.artifact, "intent": reservation.intent}}})


def row(c):
    with c.env.engine.connect() as conn:
        return conn.execute(text("SELECT * FROM runtime.runs WHERE run_id=:run"), {"run": c.run}).mappings().one()


def count(c, table):
    assert table in {"attempt_reports", "accepted_completions", "state_revisions"}
    with c.env.engine.connect() as conn:
        return conn.execute(text(f"SELECT count(*) FROM runtime.{table} WHERE run_id=:run"), {"run": c.run}).scalar_one()


def test_success_checkpoint_and_original_receipt_are_atomic(completion_env):
    c = completion_env
    c.payload["completion"]["outcome"]["checkpoint"] = c.payload["completion"]["outcome"]["outputs"][0]["artifact"]
    c.payload["expected_checkpoint_revision"] = 0
    service = CompletionCoordinator(c.env.engine, Peer())
    command = c.command("runtime.complete", c.payload)
    result = service.complete(c.env.principal, command)
    assert result.outcome.status == "accepted"
    assert service.complete(c.env.principal, command) == result
    assert row(c)["status"] == "completed" and (row(c)["spent"], row(c)["reserved"]) == (1, 0)
    assert [count(c, name) for name in ("attempt_reports", "accepted_completions", "state_revisions")] == [1, 1, 1]


def test_failure_after_acceptance_writes_rolls_back_everything(completion_env, monkeypatch):
    c = completion_env
    service = CompletionCoordinator(c.env.engine, Peer())
    command = c.command("runtime.complete", c.payload)
    service.prepare(c.env.principal, command)
    committer = CompletionCommitter(c.env.engine, "runtime")
    previous = row(c)
    original = committer.leases._changed
    def fail(*args):
        original(*args)
        raise RuntimeError("after_acceptance_writes")
    monkeypatch.setattr(committer.leases, "_changed", fail)
    with pytest.raises(RuntimeError, match="after_acceptance"):
        committer.commit(c.env.principal, command)
    assert row(c) == previous
    assert count(c, "attempt_reports") == count(c, "accepted_completions") == 0
    with c.env.engine.connect() as conn:
        assert conn.execute(text("SELECT status FROM runtime.completion_intents WHERE run_id=:run"),
                            {"run": c.run}).scalar_one() == "prepared"
    monkeypatch.setattr(committer.leases, "_changed", original)
    assert committer.commit(c.env.principal, command).outcome.status == "accepted"


@pytest.mark.parametrize("completion_env", [2], indirect=True)
def test_independent_activations_accept_despite_unrelated_run_revisions(completion_env):
    c = completion_env
    spec = c.env.raw["payload"]["invocations"][0]
    second = RuntimeLeases(c.env.engine).claim(c.env.principal, c.command("runtime.claim", {
        "run_id": c.run, "worker_id": c.env.principal.actor_id, "tool": spec["tool"], "lease_seconds": 90})).outcome.invocation
    payload = copy.deepcopy(c.payload)
    payload["completion"].update(invocation_id=second.invocation_id, attempt_id=second.attempt_id, fence=second.fence)
    commands = [c.command("runtime.complete", c.payload), c.command("runtime.complete", payload)]
    service = CompletionCoordinator(c.env.engine, Peer())
    for command in commands:
        service.prepare(c.env.principal, command)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda command: service.complete(c.env.principal, command), commands))
    assert all(r.outcome.status == "accepted" for r in results)
    assert len({r.outcome.committed.revision for r in results}) == 2
    assert count(c, "accepted_completions") == 2
    assert row(c)["status"] == "completed" and (row(c)["spent"], row(c)["reserved"]) == (2, 0)


def test_retryable_failure_records_attempt_without_consuming_canonical_result(completion_env):
    c = completion_env
    failed = copy.deepcopy(c.payload)
    failed["completion"]["outcome"] = {"status": "failed", "reason_code": "temporary", "retryable": True}
    service = CompletionCoordinator(c.env.engine, Peer())
    assert service.complete(c.env.principal, c.command("runtime.complete", failed)).outcome.status == "accepted"
    assert count(c, "attempt_reports") == 1 and count(c, "accepted_completions") == 0
    assert row(c)["status"] == "running"
    successor = RuntimeLeases(c.env.engine).claim(c.env.principal, c.command("runtime.claim", {
        "run_id": c.run, "worker_id": c.env.principal.actor_id,
        "tool": c.env.raw["payload"]["invocations"][0]["tool"], "lease_seconds": 90})).outcome.invocation
    c.payload["completion"].update(attempt_id=successor.attempt_id, fence=successor.fence)
    assert service.complete(c.env.principal, c.command("runtime.complete", c.payload)).outcome.status == "accepted"
    assert count(c, "attempt_reports") == 2 and count(c, "accepted_completions") == 1
    assert (row(c)["spent"], row(c)["reserved"]) == (2, 0)


@pytest.mark.parametrize("outcome,status,reserved,spent", [
    ({"status": "abstained", "reason_code": "not_applicable"}, "completed", 0, 1),
    ({"status": "failed", "reason_code": "invalid", "retryable": False}, "failed", 0, 1),
    ({"status": "uncertain_external_effect", "operation_id": "external", "reason_code": "uncertain"}, "blocked", 1, 0)])
def test_non_success_reports_preserve_their_meaning(completion_env, outcome, status, reserved, spent):
    c = completion_env
    c.payload["completion"]["outcome"] = outcome
    result = CompletionCoordinator(c.env.engine, Peer()).complete(c.env.principal, c.command("runtime.complete", c.payload))
    assert result.outcome.status == "accepted"
    assert row(c)["status"] == status and (row(c)["reserved"], row(c)["spent"]) == (reserved, spent)
    assert count(c, "attempt_reports") == 1


def test_terminal_blocked_run_preserves_uncertainty_without_holding_active_slot(completion_env):
    c = completion_env
    c.payload["completion"]["outcome"] = {"status": "uncertain_external_effect", "operation_id": "unknown",
                                           "reason_code": "uncertain"}
    service = CompletionCoordinator(c.env.engine, Peer())
    command = c.command("runtime.complete", c.payload)
    receipt = service.complete(c.env.principal, command)
    assert receipt.outcome.status == "accepted"
    before = row(c)
    assert before["status"] == "blocked" and before["reserved"] == 1 and before["spent"] == 0
    rejected = RuntimeLeases(c.env.engine).claim(c.env.principal, c.command("runtime.claim", {
        "run_id": c.run, "worker_id": c.env.principal.actor_id, "tool": c.invocation.tool.model_dump(), "lease_seconds": 30}))
    assert rejected.outcome.status == "rejected" and rejected.outcome.reason_code == "run_not_running"
    successor = c.env.service.admit(c.env.principal, c.command("runtime.admit_fixture", c.env.raw["payload"]))
    assert successor.outcome.status == "accepted" and successor.outcome.committed.object_id != c.run
    assert service.complete(c.env.principal, command) == receipt
    assert row(c) == before  # New campaign admission cannot settle or revive the blocked predecessor.


def test_mismatched_saved_receipt_aborts_without_result(completion_env):
    c = completion_env
    command = c.command("runtime.complete", c.payload)
    prepared = IntentPreparation(c.env.engine, "runtime").prepare(c.env.principal, command)
    reservation = prepared.reservations()[0]
    receipt = Peer().reserve(reservation).model_dump(mode="json")
    receipt["outcome"]["binding"]["intent"]["runtime_owner"] = "wrong"
    import json
    with c.env.engine.begin() as conn:
        conn.execute(text("INSERT INTO runtime.intent_reservations (tenant_id,project_id,intent_id,output_binding,receipt) "
            "VALUES (:tenant,:project,:intent,:output,CAST(:receipt AS jsonb))"), {
                "tenant": c.env.principal.scope.tenant_id, "project": c.env.principal.scope.project_id,
                "intent": prepared.intent_id, "output": reservation.intent.output_binding, "receipt": json.dumps(receipt)})
    result = CompletionCommitter(c.env.engine, "runtime").commit(c.env.principal, command)
    assert result.outcome.reason_code == "reservation_binding_mismatch"
    assert count(c, "accepted_completions") == 0 and row(c)["reserved"] == 1


def test_missing_reservation_stays_pending_then_expired_attempt_rejects(completion_env):
    c = completion_env
    command = c.command("runtime.complete", c.payload)
    IntentPreparation(c.env.engine, "runtime").prepare(c.env.principal, command)
    service = CompletionCommitter(c.env.engine, "runtime")
    assert service.commit(c.env.principal, command).outcome.status == "pending"
    with c.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.attempts SET lease_expires_at=clock_timestamp()-interval '1 second' "
                          "WHERE run_id=:run"), {"run": c.run})
    result = service.commit(c.env.principal, command)
    assert result.outcome.reason_code == "lease_expired"
    assert count(c, "attempt_reports") == 0


def test_public_completion_requires_configured_authentication(completion_env):
    c = completion_env
    command = c.command("runtime.complete", c.payload)
    credentials = RuntimeCredentials([("x" * 32, c.env.principal)])
    with TestClient(create_app(c.env.service, credentials, CompletionCoordinator(c.env.engine, Peer()))) as client:
        assert client.post("/v1/invocations/complete", content=command.canonical_bytes).status_code == 401
        headers = {"Authorization": "Bearer " + "x" * 32}
        first = client.post("/v1/invocations/complete", headers=headers, content=command.canonical_bytes)
        assert first.status_code == 200 and first.json()["outcome"]["status"] == "accepted"
        assert client.post("/v1/invocations/complete", headers=headers, content=command.canonical_bytes).json() == first.json()
    assert "/v1/invocations/complete" not in create_app().openapi()["paths"]


def test_commit_waiting_for_lock_rechecks_database_lease(completion_env):
    c = completion_env
    command = c.command("runtime.complete", c.payload)
    CompletionCoordinator(c.env.engine, Peer()).prepare(c.env.principal, command)
    name = "commit-wait-" + uuid.uuid4().hex
    engine = create_engine(c.env.engine.url, connect_args={"application_name": name, "options": "-c statement_timeout=7000"})
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            with c.env.engine.begin() as guard:
                guard.execute(text("SELECT run_id FROM runtime.runs WHERE run_id=:run FOR UPDATE"), {"run": c.run})
                future = pool.submit(CompletionCommitter(engine, "runtime").commit, c.env.principal, command)
                deadline = time.monotonic() + 5
                while True:
                    with c.env.engine.connect() as observer:
                        waiting = observer.execute(text("SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
                            "WHERE application_name=:name AND wait_event_type='Lock')"), {"name": name}).scalar_one()
                    if waiting:
                        break
                    assert time.monotonic() < deadline, "Commit did not reach held run lock"
                    time.sleep(0.01)
                guard.execute(text("UPDATE runtime.attempts SET lease_expires_at=clock_timestamp()-interval '1 second' "
                                   "WHERE run_id=:run"), {"run": c.run})
            result = future.result(timeout=10)
        assert result.outcome.reason_code == "lease_expired"
        assert count(c, "attempt_reports") == 0
    finally:
        engine.dispose()
