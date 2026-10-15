"""Actual Runtime SQL proof durability; scripted Data proof is not Data acceptance."""

import pytest
from sqlalchemy import create_engine, text
from amphora_contracts_artifact_retention import DerivedClosureReservationReceipt
from amphora_contracts_artifacts import ReservationReceipt
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.completion.commit import CompletionCommitter
from amphora_campaign_runtime.completion.prepare import IntentPreparation
from amphora_campaign_runtime.completion.profiles import RetentionProfile
from amphora_campaign_runtime.completion.closures import PROFILE
from amphora_campaign_runtime.lifecycle.pins import PinnedTools
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.resource_profiles.preflight import require_supported_resources
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.completion import closure_proofs


class DirectPeer:
    owner = "runtime"

    def reserve(self, reservation):
        raise AssertionError("Profiled run must never use ordinary reserve")


class ClosurePeer:
    calls = 0
    callback = None

    def reserve(self, reservation):
        self.calls += 1
        root = ReservationReceipt.model_validate({"outcome": {"status": "reserved", "binding": {
            "reservation_id": "r-" + reservation.intent.intent_id,
            "artifact": reservation.artifact, "intent": reservation.intent}}})
        if self.callback:
            self.callback()
        return DerivedClosureReservationReceipt(profile=PROFILE, reservation=root,
            artifact_count=7, members_sha256="d" * 64)


@pytest.fixture
def profiled_completion_env(monkeypatch, request):
    original = PinnedTools.snapshot
    monkeypatch.setattr(PinnedTools, "snapshot",
        lambda self, invocations: RetentionProfile(PROFILE).pin(original(self, invocations)))
    c = request.getfixturevalue("completion_env")
    yield c
    AuthorityCommands(c.env.engine).cancel(c.env.principal,
        c.command("runtime.cancel", {"run_id": c.run, "reason_code": "test_cleanup"}))


def test_saved_closure_survives_coordinator_and_connection_replacement(profiled_completion_env):
    c = profiled_completion_env
    peer = ClosurePeer()
    command = c.command("runtime.complete", c.payload)
    service = CompletionCoordinator(c.env.engine, DirectPeer(), closures=peer)
    assert service.prepare(c.env.principal, command).outcome.status == "pending"
    assert peer.calls == 1
    replacement = create_engine(c.env.engine.url)
    try:
        # Existing immutable proof permits completion even when current peer is unavailable.
        result = CompletionCoordinator(replacement, DirectPeer()).complete(c.env.principal, command)
        assert result.outcome.status == "accepted"
        assert peer.calls == 1
        with replacement.connect() as conn:
            proof = conn.execute(text("SELECT receipt FROM runtime.intent_retention_closures WHERE intent_id=:intent"),
                {"intent": result.outcome.binding.operation_id}).scalar_one()
        assert proof["artifact_count"] == 7 and proof["members_sha256"] == "d" * 64
    finally:
        replacement.dispose()


def test_profile_without_peer_stays_pending(profiled_completion_env):
    c = profiled_completion_env
    command = c.command("runtime.complete", c.payload)
    assert CompletionCoordinator(c.env.engine, DirectPeer()).complete(c.env.principal, command).outcome.status == "pending"
    assert CompletionCommitter(c.env.engine, "runtime").commit(c.env.principal, command).outcome.status == "pending"


def test_late_closure_after_cancel_is_durable_cleanup_evidence(profiled_completion_env):
    c = profiled_completion_env
    peer = ClosurePeer()
    peer.callback = lambda: AuthorityCommands(c.env.engine).cancel(c.env.principal,
        c.command("runtime.cancel", {"run_id": c.run, "reason_code": "stopped"}))
    command = c.command("runtime.complete", c.payload)
    result = CompletionCoordinator(c.env.engine, DirectPeer(), closures=peer).complete(c.env.principal, command)
    assert result.outcome.status == "rejected"
    with c.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.intent_retention_closures WHERE intent_id=:intent"),
            {"intent": result.outcome.binding.operation_id}).scalar_one() == 1
        assert conn.execute(text("SELECT count(*) FROM runtime.outbox o JOIN runtime.audit_events a USING(event_id) "
            "WHERE a.run_id=:run AND o.target='artifact_reconcile'"), {"run": c.run}).scalar_one() == 1


def test_downgrade_refuses_active_profile(profiled_completion_env):
    c = profiled_completion_env
    with c.env.engine.connect() as conn:
        with pytest.raises(TransitionError, match="requires_runtime_0_69"):
            require_supported_resources(conn, "0.68.0")
        require_supported_resources(conn, "0.69.0")


def test_root_only_receipt_never_authorizes_profiled_completion(profiled_completion_env):
    c = profiled_completion_env
    command = c.command("runtime.complete", c.payload)
    prepared = IntentPreparation(c.env.engine, "runtime").prepare(c.env.principal, command)
    reservation = prepared.reservations()[0]
    root = ClosurePeer().reserve(reservation).reservation
    with c.env.engine.begin() as conn:
        conn.execute(text("INSERT INTO runtime.intent_reservations "
            "(tenant_id,project_id,intent_id,output_binding,receipt) VALUES "
            "(:tenant,:project,:intent,:output,CAST(:receipt AS jsonb))"), {
            "tenant": c.env.principal.scope.tenant_id, "project": c.env.principal.scope.project_id,
            "intent": prepared.intent_id, "output": reservation.intent.output_binding,
            "receipt": root.model_dump_json()})
    assert CompletionCommitter(c.env.engine, "runtime").commit(c.env.principal, command).outcome.status == "pending"


def test_companion_write_failure_rolls_back_root_and_retry_recovers(profiled_completion_env, monkeypatch):
    c = profiled_completion_env
    command = c.command("runtime.complete", c.payload)
    peer = ClosurePeer()
    service = CompletionCoordinator(c.env.engine, DirectPeer(), closures=peer)
    original = closure_proofs.store
    def fail(*_args):
        raise RuntimeError("injected_companion_failure")
    monkeypatch.setattr(closure_proofs, "store", fail)
    with pytest.raises(RuntimeError, match="injected_companion_failure"):
        service.prepare(c.env.principal, command)
    with c.env.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.intent_reservations r "
            "JOIN runtime.completion_intents i USING(tenant_id,project_id,intent_id) WHERE i.run_id=:run"),
            {"run": c.run}).scalar_one() == 0
    monkeypatch.setattr(closure_proofs, "store", original)
    assert service.complete(c.env.principal, command).outcome.status == "accepted"
    assert peer.calls == 2
