import json
import uuid
from types import SimpleNamespace

import pytest
from amphora_contracts_artifacts import RuntimeOutcome, parse_command
from amphora_contracts_artifact_retention import parse_derived_closure_command
from amphora_contracts_core import ArtifactRef
from amphora_data_artifacts.access import Credentials
from amphora_data_artifacts.api import create_app
from amphora_data_artifacts.publication.model import Principal, UploadError
from amphora_data_artifacts.retention.outcomes import OutcomeUnavailable
from amphora_data_artifacts.retention.reservations import Reservations
from amphora_data_artifacts.retention_closures import storage
from amphora_data_artifacts.retention_closures.reservations import ClosureReservations
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError


@pytest.fixture
def closure_env(derived_env):
    d = derived_env
    leaf = d.e.publish(b"leaf")
    def derived(inputs, payload):
        final = d.stream(d.begin(inputs, payload), payload)
        response = d.client.post("/v1/artifacts/finalize", json=final, headers=d.headers)
        assert response.status_code == 200, response.text
        return ArtifactRef.model_validate(response.json()["artifact"])
    left, right = derived((leaf,), b"left"), derived((leaf,), b"right")
    root = derived((left, right), b"root")
    principal = Principal("runtime-owner", d.principal.scope, frozenset({"retention"}))
    peer = SimpleNamespace(status="prepared", calls=0)
    def lookup(binding):
        peer.calls += 1
        if peer.status == "outage":
            raise OutcomeUnavailable("runtime_outcome_unavailable")
        proof = {"status": peer.status}
        if peer.status in {"committed", "aborted"}:
            proof["runtime_receipt_id"] = "runtime-receipt"
        if peer.status == "aborted":
            proof["reason_code"] = "cancelled"
        return RuntimeOutcome.model_validate({"binding": binding.model_dump(), "proof": proof})
    peer.lookup = lookup
    return SimpleNamespace(d=d, engine=d.e.env.engine, uploads=d.e.env.uploads, principal=principal,
        root=root, members=(leaf, left, right, root), peer=peer, service=ClosureReservations(d.e.env.uploads, peer))


def command(e, family="artifacts.reserve_derived_closure", *, payload=None, key=None):
    payload = payload or {"profile": "derived-closure-retention-v1", "artifact": e.root.model_dump(mode="json"),
        "intent": {"runtime_owner": e.principal.actor_id, "intent_id": "intent", "output_binding": "result",
                   "semantic_completion_sha256": "c" * 64}}
    raw = json.dumps({"identity": {"scope": e.principal.scope.model_dump(), "actor_id": e.principal.actor_id,
                                  "command_family": family, "command_id": key or uuid.uuid4().hex}, "payload": payload})
    return parse_derived_closure_command(raw) if family == "artifacts.reserve_derived_closure" else parse_command(family, raw)


def count(e, table):
    with e.engine.connect() as conn:
        return conn.execute(text("SELECT count(*) FROM artifacts." + table +
            " WHERE tenant_id=:tenant AND project_id=:project"), e.principal.bindings).scalar_one()


def protected(e):
    with e.engine.connect() as conn:
        return set(conn.execute(text("SELECT artifact_id FROM artifacts.artifact_protection "
            "WHERE tenant_id=:tenant AND project_id=:project"), e.principal.bindings).scalars())


def test_diamond_membership_is_once_only_atomic_and_immutable(closure_env):
    e = closure_env
    request = command(e)
    receipt = e.service.reserve(e.principal, request)
    assert receipt.artifact_count == 4 and len(receipt.members_sha256) == 64
    assert protected(e) == {r.artifact_id for r in e.members}
    assert count(e, "reservations") == 1 and count(e, "retention_closure_members") == 4
    assert e.service.reserve(e.principal, request) == receipt
    assert e.service.reserve(e.principal, command(e)) == receipt
    assert e.peer.calls == 0
    for table in ("retention_closures", "retention_closure_members"):
        with pytest.raises(DBAPIError), e.engine.begin() as conn:
            conn.execute(text("DELETE FROM artifacts." + table))


@pytest.mark.parametrize("status", ["committed", "aborted"])
def test_one_root_proof_transitions_all_members(closure_env, status):
    e = closure_env
    original = command(e)
    reserved = e.service.reserve(e.principal, original)
    e.peer.status = status
    root_id = reserved.reservation.outcome.binding.reservation_id
    request = command(e, "artifacts.reconcile", payload={"reservation_id": root_id})
    result = e.service.reconcile(e.principal, request)
    assert result.outcome.status == ("confirmed" if status == "committed" else "released")
    current = e.service.get(e.principal, root_id)
    assert current.members_sha256 == reserved.members_sha256 and current.artifact_count == 4
    assert protected(e) == ({r.artifact_id for r in e.members} if status == "committed" else set())
    assert e.service.reserve(e.principal, original) == reserved
    assert e.service.reconcile(e.principal, request) == result


@pytest.mark.parametrize("status", ["prepared", "unknown", "outage"])
def test_pending_or_unreachable_runtime_cannot_release_children(closure_env, status):
    e = closure_env
    receipt = e.service.reserve(e.principal, command(e))
    e.peer.status = status
    request = command(e, "artifacts.reconcile", payload={"reservation_id": receipt.reservation.outcome.binding.reservation_id})
    with pytest.raises(OutcomeUnavailable):
        e.service.reconcile(e.principal, request)
    assert protected(e) == {r.artifact_id for r in e.members}


def test_partial_membership_failure_rolls_back_before_rejected_receipt(closure_env, monkeypatch):
    e = closure_env
    original = storage.persist
    def fail(*args):
        original(*args)
        raise UploadError("injected_after_members")
    monkeypatch.setattr(storage, "persist", fail)
    request = command(e)
    with pytest.raises(UploadError, match="injected_after_members"):
        e.service.reserve(e.principal, request)
    for table in ("reservations", "retention_closures", "retention_closure_members"):
        assert count(e, table) == 0
    monkeypatch.setattr(storage, "persist", original)
    with pytest.raises(UploadError, match="injected_after_members"):
        e.service.reserve(e.principal, request)
    assert e.service.reserve(e.principal, command(e)).artifact_count == 4


def test_existing_direct_reservation_is_not_silently_upgraded(closure_env):
    e = closure_env
    payload = json.loads(command(e).canonical_bytes)["payload"]
    del payload["profile"]
    ordinary = Reservations(e.uploads, e.peer)
    ordinary.reserve(e.principal, command(e, "artifacts.reserve", payload=payload))
    with pytest.raises(UploadError, match="reservation_profile_conflict"):
        e.service.reserve(e.principal, command(e))
    assert count(e, "retention_closures") == 0
    assert protected(e) == {e.root.artifact_id}


def test_scoped_http_reserve_and_current_readback(closure_env):
    e = closure_env
    credentials = Credentials([("r" * 32, e.principal)])
    with TestClient(create_app(e.uploads, e.d.e.env.storage, credentials, outcomes=e.peer)) as client:
        headers = {"Authorization": "Bearer " + "r" * 32, "Content-Type": "application/json"}
        request = command(e)
        response = client.post("/v1/retention-closures/reserve", content=request.canonical_bytes, headers=headers)
        assert response.status_code == 200, response.text
        body = response.json()
        path = "/v1/retention-closures/" + body["reservation"]["outcome"]["binding"]["reservation_id"]
        assert client.get(path, headers=headers).json() == body
        assert client.get(path).status_code == 401
        assert client.post("/v1/retention-closures/reserve", content=request.canonical_bytes, headers=headers).json() == body
