"""Irreversible runtime proof, terminal delivery intents and stale preparation recovery."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.completion.commit import CompletionCommitter
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.completion.prepare import IntentPreparation
from amphora_campaign_runtime.completion.recovery import StaleIntents
from amphora_campaign_runtime.completion.retention import IntentOutcomes
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.lifecycle.settlement import BudgetSettlement
from amphora_contracts_artifacts import ReservationReceipt
from amphora_contracts_core import Scope
from fastapi.testclient import TestClient
from sqlalchemy import text


class Peer:
    owner = "runtime"
    callback = None
    binding = None

    def reserve(self, reservation):
        receipt = ReservationReceipt.model_validate({"outcome": {"status": "reserved", "binding": {
            "reservation_id": "r-" + reservation.intent.intent_id + "-" + reservation.intent.output_binding,
            "artifact": reservation.artifact, "intent": reservation.intent}}})
        self.binding = receipt.outcome.binding
        if self.callback:
            self.callback()
        return receipt


def principal(c):
    return replace(c.env.principal, actions=c.env.principal.actions | {"outcome", "maintain"})


def deliveries(c):
    with c.env.engine.connect() as conn:
        return conn.execute(text("SELECT o.* FROM runtime.outbox o JOIN runtime.audit_events a USING (event_id) "
            "WHERE a.run_id=:run AND o.target LIKE 'artifact_%' ORDER BY o.operation_id"), {"run": c.run}).mappings().all()


def test_committed_proof_requires_exact_saved_binding_and_replays_delivery(completion_env):
    c = completion_env
    peer = Peer()
    service = CompletionCoordinator(c.env.engine, peer)
    command = c.command("runtime.complete", c.payload)
    accepted = service.complete(c.env.principal, command)
    outcomes = IntentOutcomes(c.env.engine, "runtime")
    proof = outcomes.lookup(principal(c), peer.binding)
    assert proof.proof.status == "committed"
    assert proof.proof.runtime_receipt_id == accepted.outcome.committed.object_id
    assert outcomes.lookup(principal(c), peer.binding.model_copy(update={"reservation_id": "wrong"})).proof.status == "unknown"
    assert len(deliveries(c)) == 1 and deliveries(c)[0]["target"] == "artifact_confirm"
    original = deliveries(c)[0]["operation_id"]
    assert service.complete(c.env.principal, command) == accepted
    assert [r["operation_id"] for r in deliveries(c)] == [original]


def test_late_reservation_after_cancel_is_reconciled_with_abort_proof(completion_env):
    c = completion_env
    peer = Peer()
    peer.callback = lambda: AuthorityCommands(c.env.engine).cancel(c.env.principal,
        c.command("runtime.cancel", {"run_id": c.run, "reason_code": "stopped"}))
    service = CompletionCoordinator(c.env.engine, peer)
    result = service.complete(c.env.principal, c.command("runtime.complete", c.payload))
    assert result.outcome.status == "rejected"
    assert [r["target"] for r in deliveries(c)] == ["artifact_reconcile"]
    proof = IntentOutcomes(c.env.engine, "runtime").lookup(principal(c), peer.binding)
    assert proof.proof.status == "aborted" and proof.proof.reason_code == "stopped"


def test_abort_proof_covers_lost_reserve_response_without_saved_receipt(completion_env):
    c = completion_env
    command = c.command("runtime.complete", c.payload)
    prepared = IntentPreparation(c.env.engine, "runtime").prepare(c.env.principal, command)
    binding = Peer().reserve(prepared.reservations()[0]).outcome.binding
    outcomes = IntentOutcomes(c.env.engine, "runtime")
    assert outcomes.lookup(principal(c), binding).proof.status == "prepared"
    AuthorityCommands(c.env.engine).cancel(c.env.principal,
        c.command("runtime.cancel", {"run_id": c.run, "reason_code": "stopped"}))
    assert outcomes.lookup(principal(c), binding).proof.status == "aborted"
    changed = binding.model_copy(update={"intent": binding.intent.model_copy(update={"semantic_completion_sha256": "f" * 64})})
    assert outcomes.lookup(principal(c), changed).proof.status == "unknown"


def test_cancel_and_commit_choose_one_irrevocable_outcome(completion_env):
    c = completion_env
    peer = Peer()
    coordinator = CompletionCoordinator(c.env.engine, peer)
    command = c.command("runtime.complete", c.payload)
    coordinator.prepare(c.env.principal, command)
    barrier = Barrier(2)
    def commit():
        barrier.wait(timeout=5)
        return CompletionCommitter(c.env.engine, "runtime").commit(c.env.principal, command)
    def cancel():
        barrier.wait(timeout=5)
        return AuthorityCommands(c.env.engine).cancel(c.env.principal,
            c.command("runtime.cancel", {"run_id": c.run, "reason_code": "stopped"}))
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.submit(commit), pool.submit(cancel)
        committed, cancelled = first.result(timeout=10), second.result(timeout=10)
    proof = IntentOutcomes(c.env.engine, "runtime").lookup(principal(c), peer.binding)
    assert (committed.outcome.status == "accepted") != (cancelled.outcome.status == "accepted")
    assert proof.proof.status == ("committed" if committed.outcome.status == "accepted" else "aborted")
    assert len(deliveries(c)) == 1
    assert deliveries(c)[0]["target"] == ("artifact_confirm" if proof.proof.status == "committed" else "artifact_reconcile")


def test_bounded_stale_intent_sweep_unblocks_once_only_settlement(completion_env):
    c = completion_env
    prepare = IntentPreparation(c.env.engine, "runtime")
    coordinator = CompletionCoordinator(c.env.engine, Peer())
    commands = [c.command("runtime.complete", c.payload) for _ in range(3)]
    for command in commands:
        coordinator.prepare(c.env.principal, command)
    recovery = StaleIntents(c.env.engine)
    assert recovery.sweep(principal(c), c.run)["aborted"] == []
    with c.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.attempts SET lease_expires_at=clock_timestamp()-interval '1 second' "
                          "WHERE run_id=:run"), {"run": c.run})
    with pytest.raises(TransitionError, match="prepared_intent"):
        BudgetSettlement(c.env.engine).sweep(principal(c), c.run)
    cursor, aborted = "", []
    while True:
        result = recovery.sweep(principal(c), c.run, after=cursor, limit=1)
        assert result["inspected"] <= 1
        aborted.extend(result["aborted"])
        if result["next_cursor"] is None:
            break
        cursor = result["next_cursor"]
    assert len(set(aborted)) == 3
    assert [r["target"] for r in deliveries(c)] == ["artifact_reconcile"] * 3
    for command in commands:
        assert prepare.prepare(c.env.principal, command).outcome.reason_code == "lease_expired"
    settlement = BudgetSettlement(c.env.engine).sweep(principal(c), c.run)
    assert (settlement.budget.spent, settlement.budget.reserved) == (1, 0)
    assert BudgetSettlement(c.env.engine).sweep(principal(c), c.run).changed is False


def test_public_outcome_is_scoped_and_requires_distinct_action(completion_env):
    c = completion_env
    peer = Peer()
    coordinator = CompletionCoordinator(c.env.engine, peer)
    coordinator.prepare(c.env.principal, c.command("runtime.complete", c.payload))
    other = replace(principal(c), scope=Scope(tenant_id=c.env.principal.scope.tenant_id, project_id="other"))
    credentials = RuntimeCredentials([("x" * 32, principal(c)), ("y" * 32, c.env.principal), ("z" * 32, other)])
    with TestClient(create_app(c.env.service, credentials, coordinator)) as client:
        path = "/v1/completion-intents/outcome"
        body = peer.binding.model_dump_json()
        assert client.post(path, content=body).status_code == 401
        for token in ("y", "z"):
            assert client.post(path, content=body, headers={"Authorization": "Bearer " + token * 32}).status_code == 403
        response = client.post(path, content=body, headers={"Authorization": "Bearer " + "x" * 32})
        assert response.status_code == 200 and response.json()["proof"]["status"] == "prepared"


def test_fault_after_terminal_queue_rolls_back_proof_receipt_and_delivery(completion_env, monkeypatch):
    c = completion_env
    peer = Peer()
    coordinator = CompletionCoordinator(c.env.engine, peer)
    command = c.command("runtime.complete", c.payload)
    coordinator.prepare(c.env.principal, command)
    committer = CompletionCommitter(c.env.engine, "runtime")
    original = committer.leases._finish
    def fail(conn, cmd, receipt):
        original(conn, cmd, receipt)
        raise RuntimeError("after_terminal_receipt")
    monkeypatch.setattr(committer.leases, "_finish", fail)
    with pytest.raises(RuntimeError, match="after_terminal"):
        committer.commit(c.env.principal, command)
    assert deliveries(c) == []
    assert IntentOutcomes(c.env.engine, "runtime").lookup(principal(c), peer.binding).proof.status == "prepared"
    monkeypatch.setattr(committer.leases, "_finish", original)
    assert committer.commit(c.env.principal, command).outcome.status == "accepted"
    assert len(deliveries(c)) == 1


def test_revocation_aborts_prepared_outputs_and_queues_reconciliation(completion_env):
    c = completion_env
    peer = Peer()
    coordinator = CompletionCoordinator(c.env.engine, peer)
    command = c.command("runtime.complete", c.payload)
    coordinator.prepare(c.env.principal, command)
    AuthorityCommands(c.env.engine).revoke(c.env.principal, c.command("runtime.revoke_worker", {
        "worker_id": c.env.principal.actor_id, "reason_code": "revoked"}))
    assert coordinator.complete(c.env.principal, command).outcome.status == "rejected"
    assert IntentOutcomes(c.env.engine, "runtime").lookup(principal(c), peer.binding).proof.status == "aborted"
    assert [r["target"] for r in deliveries(c)] == ["artifact_reconcile"]


def test_recovery_terminalizes_cancelled_command_without_caller_retry(completion_env):
    c = completion_env
    peer = Peer()
    command = c.command("runtime.complete", c.payload)
    CompletionCoordinator(c.env.engine, peer).prepare(c.env.principal, command)
    AuthorityCommands(c.env.engine).cancel(c.env.principal,
        c.command("runtime.cancel", {"run_id": c.run, "reason_code": "stopped"}))
    outcomes = IntentOutcomes(c.env.engine, "runtime")
    before = outcomes.lookup(principal(c), peer.binding)
    result = StaleIntents(c.env.engine).sweep(principal(c), c.run)
    assert result["aborted"] == [] and result["settled_commands"] == [peer.binding.intent.intent_id]
    assert outcomes.lookup(principal(c), peer.binding) == before
    with c.env.engine.connect() as conn:
        status = conn.execute(text("SELECT status FROM runtime.commands WHERE command_id=:id"),
                              {"id": command.identity.command_id}).scalar_one()
        assert status == "rejected"
    assert len(deliveries(c)) == 1
    assert StaleIntents(c.env.engine).sweep(principal(c), c.run)["inspected"] == 0
