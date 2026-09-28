"""Public historical observations with scope/actor checks and stable page membership."""

import json
from dataclasses import replace

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.completion.coordinator import CompletionCoordinator
from amphora_campaign_runtime.completion.prepare import IntentPreparation
from amphora_campaign_runtime.delivery.model import DeliveryPolicy
from amphora_campaign_runtime.delivery.store import DeliveryStore
from amphora_campaign_runtime.hosting import Host
from amphora_campaign_runtime.inspection.cursors import CursorCodec, InspectionError
from amphora_campaign_runtime.inspection.history import RuntimeHistory
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_artifacts import ReservationReceipt
from amphora_contracts_core import Scope
from fastapi.testclient import TestClient


class Peer:
    owner = "runtime"

    def reserve(self, reservation):
        return ReservationReceipt.model_validate({"outcome": {"status": "reserved", "binding": {
            "reservation_id": "r-" + reservation.intent.intent_id + "-" + reservation.intent.output_binding,
            "artifact": reservation.artifact, "intent": reservation.intent}}})


def history(c):
    return RuntimeHistory(c.env.engine, CursorCodec("x" * 32))


def test_pending_terminal_receipts_and_completion_report_are_authoritative(completion_env):
    c = completion_env
    service = history(c)
    command = c.command("runtime.complete", c.payload)
    IntentPreparation(c.env.engine, "runtime").prepare(c.env.principal, command)
    receipt = service.receipt(c.env.principal, "runtime.complete", command.identity.command_id)
    assert receipt.outcome.status == "pending"
    accepted = CompletionCoordinator(c.env.engine, Peer()).complete(c.env.principal, command)
    assert service.receipt(c.env.principal, "runtime.complete", command.identity.command_id) == accepted
    report = service.completion(c.env.principal, c.run, accepted.outcome.committed.object_id)
    assert report.canonical_result is True and report.result.outcome.status == "succeeded"
    assert report.accepted_run_revision == accepted.outcome.committed.revision
    assert len(report.retention_reservation_ids) == 1


def test_pinned_audit_pagination_and_reconnect_exclude_later_revisions(completion_env):
    c = completion_env
    service = history(c)
    first = service.audit(c.env.principal, c.run, limit=1)
    assert first.entries[0].revision == 0 and first.next_cursor is not None
    invocation = c.invocation
    RuntimeLeases(c.env.engine).renew(c.env.principal, c.command("runtime.renew", {"attempt": {
        "run_id": c.run, "invocation_id": invocation.invocation_id, "attempt_id": invocation.attempt_id,
        "fence": invocation.fence}, "lease_seconds": 90}))
    # A fresh codec with the same configured key survives a process reconnect.
    following = history(c).audit(c.env.principal, c.run, limit=1, cursor=first.next_cursor)
    assert following.snapshot_revision == first.snapshot_revision
    assert following.entries[0].revision == 1 and following.next_cursor is None
    fresh = service.audit(c.env.principal, c.run, since_revision=first.snapshot_revision)
    assert [entry.event_kind for entry in fresh.entries] == ["attempt_renewed"]
    assert fresh.snapshot_revision > first.snapshot_revision


def test_cursor_filter_scope_tamper_and_expiry_require_resnapshot(completion_env):
    c = completion_env
    clock = [1000]
    service = RuntimeHistory(c.env.engine, CursorCodec("x" * 32, ttl_seconds=60, clock=lambda: clock[0]))
    first = service.audit(c.env.principal, c.run, limit=1)
    with pytest.raises(InspectionError, match="cursor_mismatch"):
        service.audit(c.env.principal, c.run, cursor=first.next_cursor, kind="attempt_claimed")
    with pytest.raises(InspectionError, match="invalid_cursor"):
        service.audit(c.env.principal, c.run, cursor=first.next_cursor + "x")
    clock[0] += 60
    with pytest.raises(InspectionError, match="cursor_expired"):
        service.audit(c.env.principal, c.run, cursor=first.next_cursor)


def test_receipts_require_scope_and_explicit_cross_actor_inspection(completion_env):
    c = completion_env
    service = history(c)
    command = c.command("runtime.complete", c.payload)
    IntentPreparation(c.env.engine, "runtime").prepare(c.env.principal, command)
    reader = replace(c.env.principal, actor_id="inspector")
    with pytest.raises(TransitionError, match="access_denied"):
        service.receipt(reader, "runtime.complete", command.identity.command_id, c.env.principal.actor_id)
    reader = replace(reader, actions=reader.actions | {"inspect_receipts"})
    assert service.receipt(reader, "runtime.complete", command.identity.command_id, c.env.principal.actor_id).outcome.status == "pending"
    other = replace(reader, scope=Scope(tenant_id=reader.scope.tenant_id, project_id="other"))
    with pytest.raises(InspectionError, match="receipt_unavailable"):
        service.receipt(other, "runtime.complete", command.identity.command_id, c.env.principal.actor_id)
    with pytest.raises(InspectionError, match="run_unavailable"):
        service.audit(other, c.run)


def test_event_delivery_pages_expose_exhaustion_without_tokens(completion_env):
    c = completion_env
    service = history(c)
    command = c.command("runtime.complete", c.payload)
    accepted = CompletionCoordinator(c.env.engine, Peer()).complete(c.env.principal, command)
    events = service.audit(c.env.principal, c.run)
    event = next(entry for entry in events.entries if entry.event_kind == "completion_accepted")
    first = service.deliveries(c.env.principal, "run", event.event_id, limit=1)
    assert first.next_cursor is not None
    following = service.deliveries(c.env.principal, "run", event.event_id, limit=1, cursor=first.next_cursor)
    operations = {entry.operation_id for entry in (*first.entries, *following.entries)}
    assert len(operations) == 2 and accepted.outcome.committed.object_id in operations
    principal = replace(c.env.principal, actions=c.env.principal.actions | {"deliver"})
    store = DeliveryStore(c.env.engine, DeliveryPolicy(max_attempts=1))
    for claim in store.claim(principal, limit=100):
        store.finish(principal, claim, acknowledged=False)
    exact = service.delivery(c.env.principal, accepted.outcome.committed.object_id)
    assert exact.entries[0].status == "exhausted"
    assert "token" not in exact.model_dump_json() and "payload" not in exact.model_dump_json()


def test_worker_policy_delivery_lookup_needs_no_run_event(completion_env):
    c = completion_env
    command = c.command("runtime.revoke_worker", {"worker_id": "unused", "reason_code": "fixture"})
    accepted = AuthorityCommands(c.env.engine).revoke(c.env.principal, command)
    page = history(c).delivery(c.env.principal, accepted.outcome.binding.operation_id)
    assert page.journal == "policy" and page.entries[0].target == "runtime_policy_notifications"


def test_public_history_routes_bound_input_and_sanitize_cursor_failures(completion_env):
    c = completion_env
    service = history(c)
    credentials = RuntimeCredentials([("x" * 32, c.env.principal)])
    with TestClient(create_app(c.env.service, credentials, history=service)) as client:
        headers = {"Authorization": "Bearer " + "x" * 32}
        path = f"/v1/runs/{c.run}/audit"
        assert client.get(path).status_code == 401
        assert client.get(path + "?limit=101", headers=headers).status_code == 422
        bad = client.get(path + "?cursor=private-content", headers=headers)
        assert bad.status_code == 409 and bad.json()["resnapshot"] is True
        assert "private-content" not in bad.text
        page = client.get(path + "?limit=1", headers=headers)
        assert page.status_code == 200 and page.json()["next_cursor"]
    assert "/v1/runs/{run_id}/audit" not in create_app().openapi()["paths"]


def test_historical_claim_receipt_does_not_restore_revoked_authority(completion_env):
    c = completion_env
    service = history(c)
    original = service.receipt(c.env.principal, "runtime.claim", c.claim_command.identity.command_id)
    assert original.outcome.status == "claimed"
    AuthorityCommands(c.env.engine).revoke(c.env.principal, c.command("runtime.revoke_worker", {
        "worker_id": c.env.principal.actor_id, "reason_code": "revoked"}))
    assert service.receipt(c.env.principal, "runtime.claim", c.claim_command.identity.command_id) == original
    attempt = {key: getattr(c.invocation, key) for key in ("run_id", "invocation_id", "attempt_id", "fence")}
    renewed = RuntimeLeases(c.env.engine).renew(c.env.principal, c.command("runtime.renew", {"attempt": attempt}))
    assert renewed.outcome.reason_code == "worker_revoked"


def test_host_requires_stable_explicit_cursor_key(completion_env, tmp_path, monkeypatch):
    c = completion_env
    monkeypatch.setenv("TEST_HISTORY_DATABASE", c.env.engine.url.render_as_string(hide_password=False))
    monkeypatch.setenv("TEST_HISTORY_TOKEN", "x" * 32)
    monkeypatch.setenv("TEST_CURSOR_KEY", "k" * 32)
    raw = {"database_url_env": "TEST_HISTORY_DATABASE", "fixtures": [c.env.raw["payload"]], "principals": [
        {"token_env": "TEST_HISTORY_TOKEN", "actor_id": c.env.principal.actor_id,
         "scope": c.env.principal.scope.model_dump(), "actions": ["read"]}],
        "inspection": {"cursor_key_env": "TEST_CURSOR_KEY", "ttl_seconds": 900}}
    path = tmp_path / "inspection.json"
    path.write_text(json.dumps(raw))
    host = Host.load(path)
    try:
        assert "/v1/runs/{run_id}/audit" in host.app().openapi()["paths"]
    finally:
        host.close()
    monkeypatch.setenv("TEST_CURSOR_KEY", "short")
    with pytest.raises(ValueError, match="cursor key"):
        Host.load(path)
