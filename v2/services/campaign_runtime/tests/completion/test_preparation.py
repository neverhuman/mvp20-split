"""Immutable intent identity, authority, reservation resume and cancellation races."""

import copy
from concurrent.futures import ThreadPoolExecutor

import pytest
from amphora_campaign_runtime.completion.artifacts import ReservationUnavailable
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.completion.model import CompletionProposal, PreparedIntent
from amphora_campaign_runtime.completion.prepare import IntentPreparation
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.persistence.commands import CommandConflict
from amphora_contracts_artifacts import ReservationReceipt
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError


class Peer:
    owner = "runtime"
    calls = 0
    outage = False
    callback = None

    def reserve(self, reservation):
        self.calls += 1
        if self.outage:
            raise ReservationUnavailable("outage")
        if self.callback:
            self.callback()
        return ReservationReceipt.model_validate({"outcome": {"status": "reserved", "binding": {
            "reservation_id": "reservation-" + reservation.intent.output_binding,
            "artifact": reservation.artifact, "intent": reservation.intent}}})


def state(c):
    with c.env.engine.connect() as conn:
        return conn.execute(text("SELECT * FROM runtime.completion_intents WHERE run_id=:run"),
                            {"run": c.run}).mappings().all()


def test_duplicate_preparation_reuses_immutable_intent(completion_env):
    c = completion_env
    command = c.command("runtime.complete", c.payload)
    service = IntentPreparation(c.env.engine, "runtime")
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda _: service.prepare(c.env.principal, command), range(2)))
    assert replies[0] == replies[1] and isinstance(replies[0], PreparedIntent)
    assert len(state(c)) == 1
    assert state(c)[0]["semantic_sha256"] == replies[0].proposal.digest
    changed = copy.deepcopy(c.payload)
    changed["completion"]["outcome"]["outputs"][0]["artifact"]["sha256"] = "d" * 64
    with pytest.raises(CommandConflict):
        service.prepare(c.env.principal, c.command("runtime.complete", changed, command.identity.command_id))


def test_semantic_digest_ignores_command_id_but_pins_output(completion_env):
    c = completion_env
    first = CompletionProposal.from_command(c.command("runtime.complete", c.payload))
    second = CompletionProposal.from_command(c.command("runtime.complete", c.payload))
    assert first.digest == second.digest
    changed = copy.deepcopy(c.payload)
    changed["completion"]["outcome"]["outputs"][0]["artifact"]["sha256"] = "d" * 64
    assert CompletionProposal.from_command(c.command("runtime.complete", changed)).digest != first.digest


@pytest.mark.parametrize("fault,reason", [("output", "unknown_output"), ("schema", "output_binding_mismatch"),
    ("duplicate", "duplicate_output"), ("checkpoint", "checkpoint_revision_conflict"), ("fence", "stale_attempt")])
def test_invalid_proposals_do_not_prepare(completion_env, fault, reason):
    c = completion_env
    payload = copy.deepcopy(c.payload)
    outcome = payload["completion"]["outcome"]
    if fault == "output":
        # Keep the required port too, so the unknown-port oracle is distinct.
        outcome["outputs"].append({**outcome["outputs"][0], "port": "unknown"})
    elif fault == "schema":
        outcome["outputs"][0]["artifact"]["schema_ref"]["sha256"] = "d" * 64
    elif fault == "duplicate":
        outcome["outputs"].append(outcome["outputs"][0])
    elif fault == "checkpoint":
        payload["expected_checkpoint_revision"] = 99
    else:
        payload["completion"]["fence"] += 1
    response = IntentPreparation(c.env.engine, "runtime").prepare(c.env.principal, c.command("runtime.complete", payload))
    assert response.outcome.reason_code == reason
    assert state(c) == []


def test_reservations_resume_outside_locks_and_cancel_irreversibly(completion_env):
    c = completion_env
    peer = Peer()
    coordinator = CompletionCoordinator(c.env.engine, peer)
    command = c.command("runtime.complete", c.payload)
    peer.outage = True
    assert coordinator.prepare(c.env.principal, command).outcome.status == "pending"
    assert state(c)[0]["status"] == "prepared"
    peer.outage = False
    # A second connection takes runtime locks during the remote call. Any held run lock would time out.
    peer.callback = lambda: AuthorityCommands(c.env.engine).cancel(c.env.principal,
        c.command("runtime.cancel", {"run_id": c.run, "reason_code": "cancelled"}))
    result = coordinator.prepare(c.env.principal, command)
    assert result.outcome.status == "rejected" and result.outcome.reason_code == "cancelled"
    assert state(c)[0]["status"] == "aborted"
    assert coordinator.prepare(c.env.principal, command) == result
    assert peer.calls == 2


def test_acquired_receipts_are_reused_and_pinned_contract_is_immutable(completion_env):
    c = completion_env
    peer = Peer()
    coordinator = CompletionCoordinator(c.env.engine, peer)
    command = c.command("runtime.complete", c.payload)
    first = coordinator.prepare(c.env.principal, command)
    assert first.outcome.status == "pending"
    assert coordinator.prepare(c.env.principal, command) == first
    assert peer.calls == 1
    with c.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.intent_reservations WHERE intent_id=:intent"),
            {"intent": state(c)[0]["intent_id"]}).scalar_one() == 1
    with pytest.raises(DBAPIError), c.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.runs SET tool_snapshot='{}' WHERE run_id=:run"), {"run": c.run})


def test_expired_prepared_intent_aborts_before_reclaim(completion_env):
    c = completion_env
    service = IntentPreparation(c.env.engine, "runtime")
    command = c.command("runtime.complete", c.payload)
    assert isinstance(service.prepare(c.env.principal, command), PreparedIntent)
    with c.env.engine.begin() as conn:
        conn.execute(text("UPDATE runtime.attempts SET lease_expires_at=clock_timestamp()-interval '1 second' "
                          "WHERE run_id=:run"), {"run": c.run})
    result = service.prepare(c.env.principal, command)
    assert result.outcome.reason_code == "lease_expired"
    assert state(c)[0]["status"] == "aborted"


def test_partial_reservation_resume_does_not_reacquire_saved_output(completion_env):
    c = completion_env
    c.payload["completion"]["outcome"]["checkpoint"] = c.payload["completion"]["outcome"]["outputs"][0]["artifact"]
    class InterruptedPeer(Peer):
        def reserve(self, reservation):
            if self.calls == 1:
                self.calls += 1
                raise ReservationUnavailable("lost_second_response")
            return super().reserve(reservation)
    peer = InterruptedPeer()
    coordinator = CompletionCoordinator(c.env.engine, peer)
    command = c.command("runtime.complete", c.payload)
    assert coordinator.prepare(c.env.principal, command).outcome.status == "pending"
    with c.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.intent_reservations WHERE intent_id=:intent"),
            {"intent": state(c)[0]["intent_id"]}).scalar_one() == 1
    assert coordinator.prepare(c.env.principal, command).outcome.status == "pending"
    assert peer.calls == 3


def test_preparation_failure_rolls_back_intent_audit_and_revision(completion_env, monkeypatch):
    c = completion_env
    service = IntentPreparation(c.env.engine, "runtime")
    command = c.command("runtime.complete", c.payload)
    original = service.leases._changed
    def fail(*args):
        original(*args)
        raise RuntimeError("injected_after_intent_and_event")
    monkeypatch.setattr(service.leases, "_changed", fail)
    with pytest.raises(RuntimeError, match="injected"):
        service.prepare(c.env.principal, command)
    assert state(c) == []
    with c.env.engine.connect() as conn:
        assert conn.execute(text("SELECT revision FROM runtime.runs WHERE run_id=:run"), {"run": c.run}).scalar_one() == 1
        assert conn.execute(text("SELECT status FROM runtime.commands WHERE command_id=:id"),
                            {"id": command.identity.command_id}).scalar_one() == "pending"
    monkeypatch.setattr(service.leases, "_changed", original)
    assert isinstance(service.prepare(c.env.principal, command), PreparedIntent)
