"""Authority commands serialize with claims/renewals and atomically abort intents."""

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials, RuntimePrincipal
from amphora_campaign_runtime.lifecycle.authority import AuthorityCommands
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_runtime import parse_command
from fastapi.testclient import TestClient
from sqlalchemy import event, text


def command(e, family, payload, principal=None):
    principal = principal or e.principal
    return parse_command(family, json.dumps({"identity": {"command_family": family,
        "command_id": uuid.uuid4().hex, "actor_id": principal.actor_id, "scope": principal.scope.model_dump()},
        "payload": payload}))


def prepared(e):
    e.principal = replace(e.principal, actions=e.principal.actions | {"cancel", "revoke", "maintain"})
    run = e.service.admit(e.principal, command(e, "runtime.admit_fixture", e.raw["payload"])).outcome.committed.object_id
    return run


def claim(e, run, principal=None):
    principal = principal or e.principal
    return RuntimeLeases(e.engine).claim(principal, command(e, "runtime.claim", {"run_id": run,
        "worker_id": principal.actor_id, "tool": e.raw["payload"]["invocations"][0]["tool"]}, principal))


def row(e, run):
    with e.engine.connect() as conn:
        return conn.execute(text("SELECT * FROM runtime.runs WHERE run_id=:run"), {"run": run}).mappings().one()


def intent(e, run, issued):
    invocation = issued.invocation
    identity = uuid.uuid4().hex
    with e.engine.begin() as conn:
        conn.execute(text("INSERT INTO runtime.completion_intents "
            "(tenant_id,project_id,intent_id,run_id,activation_id,attempt_id,fence,operation_id,semantic_sha256,output_bindings,status) "
            "VALUES (:tenant,:project,:intent,:run,:activation,:attempt,:fence,:operation,:digest,'{}','prepared')"),
            {"tenant": e.principal.scope.tenant_id, "project": e.principal.scope.project_id,
             "intent": identity, "run": run, "activation": invocation.activation_id,
             "attempt": invocation.attempt_id, "fence": invocation.fence,
             "operation": issued.receipt.binding.operation_id, "digest": "b" * 64})
    return identity


def test_cancel_aborts_prepared_intent_and_settles_atomically(fixture_env):
    e = fixture_env
    run = prepared(e)
    issued = claim(e, run).outcome
    intent_id = intent(e, run, issued)
    service = AuthorityCommands(e.engine)
    cmd = command(e, "runtime.cancel", {"run_id": run, "reason_code": "operator_stop"})
    receipt = service.cancel(e.principal, cmd)
    assert receipt.outcome.status == "accepted"
    assert service.cancel(e.principal, cmd) == receipt
    state = row(e, run)
    assert (state["status"], state["reserved"], state["spent"]) == ("cancelled", 0, 1)
    with e.engine.connect() as conn:
        proof = conn.execute(text("SELECT outcome FROM runtime.completion_intents WHERE intent_id=:intent"),
                             {"intent": intent_id}).scalar_one()
    assert proof == {"status": "aborted", "runtime_receipt_id": receipt.outcome.binding.operation_id,
                     "reason_code": "operator_stop"}
    assert claim(e, run).outcome.reason_code == "run_not_running"


def test_cancel_revision_and_action_grants_are_enforced(fixture_env):
    e = fixture_env
    run = prepared(e)
    claim(e, run)
    cmd = command(e, "runtime.cancel", {"run_id": run, "expected_run_revision": 0, "reason_code": "stop"})
    result = AuthorityCommands(e.engine).cancel(e.principal, cmd)
    assert result.outcome.reason_code == "run_revision_conflict"
    with pytest.raises(TransitionError, match="access_denied"):
        AuthorityCommands(e.engine).cancel(replace(e.principal, actions=frozenset()), cmd)
    assert row(e, run)["status"] == "running"


def test_revoke_without_any_run_has_durable_policy_audit(fixture_env):
    e = fixture_env
    principal = replace(e.principal, actions=frozenset({"revoke"}))
    cmd = command(e, "runtime.revoke_worker", {"worker_id": "future-worker", "reason_code": "revoked"})
    service = AuthorityCommands(e.engine)
    result = service.revoke(principal, cmd)
    assert result.outcome.committed.kind == "worker_policy"
    assert result.outcome.committed.revision == 1
    assert service.revoke(principal, cmd) == result
    with e.engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM runtime.policy_audit_events WHERE operation_id=:operation"),
                             {"operation": result.outcome.binding.operation_id}).scalar_one()
    assert count == 1


def test_revoked_attempt_cannot_renew_and_other_worker_gets_new_fence(fixture_env):
    e = fixture_env
    run = prepared(e)
    first = claim(e, run).outcome.invocation
    service = AuthorityCommands(e.engine)
    cmd = command(e, "runtime.revoke_worker", {"worker_id": e.principal.actor_id, "reason_code": "revoked"})
    receipt = service.revoke(e.principal, cmd)
    assert claim(e, run).outcome.reason_code == "worker_revoked"
    renew = command(e, "runtime.renew", {"attempt": {"run_id": run, "invocation_id": first.invocation_id,
        "attempt_id": first.attempt_id, "fence": first.fence}})
    assert RuntimeLeases(e.engine).renew(e.principal, renew).outcome.reason_code == "worker_revoked"
    other = RuntimePrincipal("worker-2", e.principal.scope, frozenset({"claim"}))
    second = claim(e, run, other).outcome.invocation
    assert second.fence == first.fence + 1 and second.attempt_id != first.attempt_id
    assert service.revoke(e.principal, cmd) == receipt
    assert (row(e, run)["reserved"], row(e, run)["spent"]) == (1, 1)


def test_cancel_and_claim_race_preserves_accounting(fixture_env):
    e = fixture_env
    run = prepared(e)
    barrier = Barrier(2)

    def cancel():
        barrier.wait(timeout=10)
        return AuthorityCommands(e.engine).cancel(e.principal,
            command(e, "runtime.cancel", {"run_id": run, "reason_code": "stop"}))

    def acquire():
        barrier.wait(timeout=10)
        return claim(e, run)

    with ThreadPoolExecutor(max_workers=2) as pool:
        stop, issued = pool.submit(cancel), pool.submit(acquire)
        assert stop.result(timeout=15).outcome.status == "accepted"
        acquisition = issued.result(timeout=15)
    state = row(e, run)
    assert state["status"] == "cancelled" and state["reserved"] == 0
    assert state["spent"] == (1 if acquisition.outcome.status == "claimed" else 0)


def test_abort_rolls_back_if_budget_commit_fails(fixture_env):
    e = fixture_env
    run = prepared(e)
    intent_id = intent(e, run, claim(e, run).outcome)

    def fault(_conn, _cursor, statement, *_args):
        if statement.startswith("UPDATE runtime.runs SET revision="):
            raise RuntimeError("injected cancellation fault")

    event.listen(e.engine, "after_cursor_execute", fault)
    cmd = command(e, "runtime.cancel", {"run_id": run, "reason_code": "stop"})
    try:
        with pytest.raises(RuntimeError, match="injected"):
            AuthorityCommands(e.engine).cancel(e.principal, cmd)
    finally:
        event.remove(e.engine, "after_cursor_execute", fault)
    assert (row(e, run)["status"], row(e, run)["reserved"]) == ("running", 1)
    with e.engine.connect() as conn:
        assert conn.execute(text("SELECT status FROM runtime.completion_intents WHERE intent_id=:intent"),
                            {"intent": intent_id}).scalar_one() == "prepared"
    assert AuthorityCommands(e.engine).cancel(e.principal, cmd).outcome.status == "accepted"


def test_public_cancel_route(fixture_env):
    e = fixture_env
    run = prepared(e)
    credentials = RuntimeCredentials([("a" * 32, e.principal)])
    cmd = command(e, "runtime.cancel", {"run_id": run, "reason_code": "stop"})
    with TestClient(create_app(e.service, credentials)) as client:
        assert client.post("/v1/runs/cancel", content=cmd.canonical_bytes).status_code == 401
        response = client.post("/v1/runs/cancel", content=cmd.canonical_bytes,
                               headers={"Authorization": "Bearer " + "a" * 32})
        assert response.json()["outcome"]["status"] == "accepted"


def test_revocation_and_renewal_race_never_restores_authority(fixture_env):
    e = fixture_env
    run = prepared(e)
    invocation = claim(e, run).outcome.invocation
    barrier = Barrier(2)

    def revoke():
        barrier.wait(timeout=10)
        return AuthorityCommands(e.engine).revoke(e.principal,
            command(e, "runtime.revoke_worker", {"worker_id": e.principal.actor_id, "reason_code": "revoked"}))

    def renewal():
        barrier.wait(timeout=10)
        return RuntimeLeases(e.engine).renew(e.principal, command(e, "runtime.renew", {"attempt": {
            "run_id": run, "invocation_id": invocation.invocation_id,
            "attempt_id": invocation.attempt_id, "fence": invocation.fence}}))

    with ThreadPoolExecutor(max_workers=2) as pool:
        revoked, renewed = pool.submit(revoke), pool.submit(renewal)
        assert revoked.result(timeout=15).outcome.status == "accepted"
        assert renewed.result(timeout=15).outcome.status in {"accepted", "rejected"}
    assert claim(e, run).outcome.reason_code == "worker_revoked"
    assert (row(e, run)["reserved"], row(e, run)["spent"]) == (0, 1)


def test_uncertainty_stops_without_refunding(fixture_env):
    e = fixture_env
    run = prepared(e)
    invocation = claim(e, run).outcome.invocation
    with e.engine.begin() as conn:
        # Fixture models an uncertain tool report; completion transport belongs to .05.
        conn.execute(text("UPDATE runtime.attempts SET status='uncertain' WHERE run_id=:run AND attempt_id=:attempt"),
                     {"run": run, "attempt": invocation.attempt_id})
        conn.execute(text("UPDATE runtime.activations SET status='uncertain' WHERE run_id=:run"), {"run": run})
    result = AuthorityCommands(e.engine).cancel(e.principal,
        command(e, "runtime.cancel", {"run_id": run, "reason_code": "stop"}))
    assert result.outcome.status == "accepted"
    assert (row(e, run)["status"], row(e, run)["reserved"], row(e, run)["spent"]) == ("blocked", 1, 0)
    assert claim(e, run).outcome.reason_code == "run_not_running"


def test_wrong_scope_cannot_cancel_guessed_run(fixture_env):
    e = fixture_env
    run = prepared(e)
    other = replace(e.principal, scope=e.principal.scope.model_copy(update={"project_id": "other-project"}))
    result = AuthorityCommands(e.engine).cancel(other,
        command(e, "runtime.cancel", {"run_id": run, "reason_code": "stop"}, other))
    assert result.outcome.reason_code == "run_unavailable"
    assert row(e, run)["status"] == "running"
