"""Artifact-owned handshake probes; scripted peer is not runtime integration evidence."""

import json
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from amphora_contracts_artifacts import RuntimeOutcome, parse_command
from amphora_data_artifacts.access import Credentials
from amphora_data_artifacts.api import create_app
from amphora_data_artifacts.maintenance.reconcile import Reconciler
from amphora_data_artifacts.publication.finalize import Finalizer
from amphora_data_artifacts.publication.model import UploadError
from amphora_data_artifacts.retention.outcomes import OutcomeUnavailable, RuntimeOutcomes
from amphora_data_artifacts.retention.reservations import Reservations
from fastapi.testclient import TestClient
from sqlalchemy import event, text

pytestmark = pytest.mark.postgres


def command(env, family, payload, command_id=None):
    return parse_command(family, json.dumps({"identity": {"command_family": family,
        "command_id": command_id or uuid.uuid4().hex, "actor_id": env.principal.actor_id,
        "scope": env.principal.scope.model_dump()}, "payload": payload}))


@pytest.fixture
def retained(upload_env):
    env = upload_env
    upload = env.begin()
    attempt = env.uploads.start(env.principal, upload.upload_id)
    writer = env.storage.writer(attempt)
    writer.write(b"data")
    writer.seal()
    writer.close()
    env.uploads.finish(env.principal, attempt, verified=True, actual_bytes=4)
    artifact = Finalizer(env.uploads, env.storage).finalize(env.principal,
        command(env, "artifacts.finalize", {"upload_id": upload.upload_id,
                                          "content": upload.content.model_dump()})).artifact
    env.principal = replace(env.principal, actions=frozenset({"retention"}))
    peer = SimpleNamespace(status="prepared", receipt="runtime-commit", calls=0)

    def lookup(binding):
        peer.calls += 1
        if peer.status == "outage":
            raise OutcomeUnavailable("runtime_outcome_unavailable")
        proof = {"status": peer.status}
        if peer.status in {"committed", "aborted"}:
            proof["runtime_receipt_id"] = peer.receipt
        if peer.status == "aborted":
            proof["reason_code"] = "cancelled"
        return RuntimeOutcome.model_validate({"binding": binding.model_dump(), "proof": proof})

    peer.lookup = lookup
    service = Reservations(env.uploads, peer)
    payload = {"artifact": artifact.model_dump(), "intent": {"runtime_owner": env.principal.actor_id,
        "intent_id": "intent-1", "output_binding": "out", "semantic_completion_sha256": "b" * 64}}
    return env, service, peer, payload


def reserve(fixture, payload=None, command_id=None):
    env, service, _, original = fixture
    return service.reserve(env.principal, command(env, "artifacts.reserve", payload or original, command_id))


def test_reservation_identity_replay_concurrency_and_conflict(retained):
    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(lambda _: reserve(retained), range(2)))
    assert receipts[0] == receipts[1]
    assert reserve(retained, command_id="same") == reserve(retained, command_id="same")
    changed = json.loads(json.dumps(retained[3]))
    changed["intent"]["semantic_completion_sha256"] = "c" * 64
    with pytest.raises(UploadError, match="reservation_identity_conflict"):
        reserve(retained, changed)


@pytest.mark.parametrize("status", ["prepared", "unknown", "outage"])
def test_uncertainty_preserves_pending_command_and_protection(retained, status):
    env, service, peer, _ = retained
    binding = reserve(retained).outcome.binding
    cmd = command(env, "artifacts.reconcile", {"reservation_id": binding.reservation_id})
    peer.status = status
    with pytest.raises(OutcomeUnavailable):
        service.reconcile(env.principal, cmd)
    assert reserve(retained).outcome.status == "reserved"
    peer.status = "committed"
    assert service.reconcile(env.principal, cmd).outcome.status == "confirmed"
    calls = peer.calls
    peer.status = "outage"
    assert service.reconcile(env.principal, cmd).outcome.status == "confirmed"
    assert peer.calls == calls


def test_confirm_requires_exact_receipt_and_terminal_abort_cannot_revive(retained):
    env, service, peer, _ = retained
    binding = reserve(retained).outcome.binding
    peer.status = "committed"
    bad = command(env, "artifacts.confirm", {"reservation_id": binding.reservation_id,
                    "intent_id": "intent-1", "runtime_receipt_id": "wrong"})
    with pytest.raises(UploadError, match="confirmation_proof_mismatch"):
        service.reconcile(env.principal, bad)
    peer.status = "aborted"
    cmd = command(env, "artifacts.reconcile", {"reservation_id": binding.reservation_id})
    assert service.reconcile(env.principal, cmd).outcome.status == "released"
    assert reserve(retained).outcome.status == "released"
    peer.status = "committed"
    with pytest.raises(UploadError, match="runtime_outcome_conflict"):
        service.reconcile(env.principal, command(env, "artifacts.reconcile", {"reservation_id": binding.reservation_id}))


def test_shared_artifact_bindings_are_independently_protected(retained):
    env, service, peer, payload = retained
    first = reserve(retained).outcome.binding
    other = json.loads(json.dumps(payload))
    other["intent"]["intent_id"] = "intent-2"
    second = reserve(retained, other).outcome.binding
    peer.status = "aborted"
    service.reconcile(env.principal, command(env, "artifacts.reconcile", {"reservation_id": first.reservation_id}))
    assert reserve(retained, other).outcome.status == "reserved"
    assert first.reservation_id != second.reservation_id
    with env.engine.connect() as conn:
        rows = conn.execute(text("SELECT status FROM artifacts.reservations WHERE tenant_id=:tenant AND project_id=:project"),
                            env.principal.bindings).scalars().all()
    assert sorted(rows) == ["released", "reserved"]


def test_scope_actor_and_descriptor_cannot_be_forged(retained):
    env, service, _, payload = retained
    cmd = command(env, "artifacts.reserve", payload)
    with pytest.raises(UploadError, match="access_denied"):
        service.reserve(replace(env.principal, actor_id="impostor"), cmd)
    forged = json.loads(json.dumps(payload))
    forged["artifact"]["size_bytes"] = 999
    with pytest.raises(UploadError, match="artifact_descriptor_conflict"):
        reserve(retained, forged)


@pytest.mark.parametrize("mode", ["committed", "aborted", "mismatch", "bad-credential"])
def test_authenticated_separate_runtime_peer(retained, mode):
    env, service, _, _ = retained
    binding = reserve(retained).outcome.binding
    proof = {"status": "aborted" if mode == "aborted" else "committed", "runtime_receipt_id": "receipt-1"}
    if mode == "aborted":
        proof["reason_code"] = "cancelled"
    child = subprocess.Popen([sys.executable, "-I", str(Path(__file__).with_name("runtime_probe.py"))],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        child.stdin.write(json.dumps({"token": "x" * 32, "proof": proof, "mismatch": mode == "mismatch"}) + "\n")
        child.stdin.flush()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(child.stdout.readline)
            try:
                port = int(future.result(timeout=15))
            except BaseException:
                child.kill()
                raise
        service.outcomes = RuntimeOutcomes("worker", f"http://127.0.0.1:{port}/outcome",
                                          ("y" if mode == "bad-credential" else "x") * 32)
        cmd = command(env, "artifacts.reconcile", {"reservation_id": binding.reservation_id})
        if mode in {"mismatch", "bad-credential"}:
            with pytest.raises(OutcomeUnavailable):
                service.reconcile(env.principal, cmd)
            assert reserve(retained).outcome.status == "reserved"
        else:
            result = service.reconcile(env.principal, cmd)
            assert result.outcome.status == ("released" if mode == "aborted" else "confirmed")
    finally:
        child.kill()
        child.communicate(timeout=10)


def test_exact_confirmation_and_original_reservation_receipt(retained):
    env, service, peer, _ = retained
    original = reserve(retained, command_id="original")
    peer.status = "committed"
    receipt = service.reconcile(env.principal, command(env, "artifacts.confirm",
        {"reservation_id": original.outcome.binding.reservation_id, "intent_id": "intent-1",
         "runtime_receipt_id": peer.receipt}))
    assert receipt.outcome.status == "confirmed"
    assert reserve(retained, command_id="original") == original
    assert reserve(retained).outcome.status == "confirmed"


def test_http_grants_pending_retry_and_confirm(retained):
    env, _, peer, payload = retained
    credentials = Credentials([("r" * 32, env.principal)])
    headers = {"Authorization": "Bearer " + "r" * 32}
    with TestClient(create_app(env.uploads, env.storage, credentials, peer)) as client:
        raw = command(env, "artifacts.reserve", payload).canonical_bytes
        assert client.post("/v1/reservations", content=raw).status_code == 401
        reply = client.post("/v1/reservations", content=raw, headers=headers)
        assert reply.status_code == 200
        binding = reply.json()["outcome"]["binding"]
        raw = command(env, "artifacts.confirm", {"reservation_id": binding["reservation_id"],
            "intent_id": "intent-1", "runtime_receipt_id": peer.receipt}).canonical_bytes
        assert client.post("/v1/reservations/confirm", content=raw, headers=headers).status_code == 503
        peer.status = "committed"
        response = client.post("/v1/reservations/confirm", content=raw, headers=headers)
        assert response.json()["outcome"]["status"] == "confirmed"


def test_terminal_transition_and_receipt_rollback_together(retained):
    env, service, peer, _ = retained
    binding = reserve(retained).outcome.binding
    peer.status = "aborted"
    cmd = command(env, "artifacts.reconcile", {"reservation_id": binding.reservation_id})

    def fault(_conn, _cursor, statement, *_args):
        if statement.startswith("UPDATE artifacts.reservations SET status="):
            raise RuntimeError("injected terminal transaction fault")

    event.listen(env.engine, "after_cursor_execute", fault)
    try:
        with pytest.raises(RuntimeError, match="injected"):
            service.reconcile(env.principal, cmd)
    finally:
        event.remove(env.engine, "after_cursor_execute", fault)
    assert reserve(retained).outcome.status == "reserved"
    assert service.reconcile(env.principal, cmd).outcome.status == "released"


def test_bounded_sweep_late_reservation_and_retry(retained):
    env, service, peer, _ = retained
    peer.status = "aborted"  # Immutable tombstone predates late reserve.
    binding = reserve(retained).outcome.binding
    runner = Reconciler(service)
    assert runner.sweep(env.principal, limit=1)["released"] == 1
    assert reserve(retained).outcome.status == "released"
    peer.status = "committed"  # Scripted contradiction must not revive terminal binding.
    assert runner.sweep(env.principal)["confirmed"] == 0
    with pytest.raises(UploadError, match="runtime_outcome_conflict"):
        service.reconcile(env.principal, command(env, "artifacts.reconcile", {"reservation_id": binding.reservation_id}))


def test_bounded_sweep_unknown_reuses_pending_command(retained):
    env, service, peer, _ = retained
    reserve(retained)
    runner = Reconciler(service)
    peer.status = "outage"
    assert runner.sweep(env.principal)["deferred"] == 1
    assert runner.sweep(env.principal)["deferred"] == 1
    peer.status = "committed"
    assert runner.sweep(env.principal)["confirmed"] == 1
    with env.engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM artifacts.commands WHERE tenant_id=:tenant "
            "AND project_id=:project AND family='artifacts.reconcile'"), env.principal.bindings).scalar_one()
    assert count == 1
