"""Real persistence preserves pins through lifecycle and explicit denial."""

import copy
from dataclasses import replace

import pytest
from amphora_capability_registry.catalog.model import Lifecycle, RegistryDenied
from sqlalchemy import text

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("action", ["drain", "revoke", "drain_deployment", "revoke_deployment"])
def test_lifecycle_removes_capacity_without_rewriting_pins_or_old_receipts(installed, action):
    case = installed
    assert case.heartbeat().status == "accepted"
    first = case.env.execute("resolve", case.need, command_id="selected")
    assert first.decision.status == "candidate"
    if action.endswith("_deployment"):
        payload = {"deployment_id": "d1", "expected_revision": 1}
    else:
        payload = {"release": case.lock, "expected_revision": 2}
    changed = case.env.execute(action, payload)
    assert changed.status == "accepted"
    assert case.env.execute("resolve", case.need).status == "rejected"
    assert case.env.execute("resolve", case.need, command_id="selected") == first
    retained = case.env.registry.read_release(case.env.admin, case.lock["descriptor_sha256"])
    assert retained.lock.model_dump(mode="json") == case.lock
    assert case.heartbeat(expected_revision=1).reason_code == "deployment_not_active"
    if action in {"drain", "revoke"}:
        assert case.env.execute("activate", {"release": case.lock, "expected_revision": 3}).reason_code == "lifecycle_transition_denied"
    else:
        old = case.env.execute("deploy", case.deployment)
        assert old.reason_code == "existing" and old.deployment.status != "active"


@pytest.mark.parametrize("fault,reason", [("wrong_revision", "revision_conflict"), ("unlisted_worker", "replica_worker_denied"),
    ("wrong_owner", "replica_owner_conflict"), ("too_many_slots", "replica_capacity_exceeded")])
def test_heartbeat_authority_and_revision_cannot_be_overwritten(installed, fault, reason):
    case = installed
    first = case.heartbeat()
    payload = {"deployment_id": "d1", "replica_id": "r1", "expected_revision": 1, "free_slots": 1, "ttl_seconds": 30}
    actor = case.env.worker
    if fault == "wrong_revision":
        payload["expected_revision"] = 0
    elif fault == "unlisted_worker":
        actor = replace(actor, actor_id="unlisted")
    elif fault == "wrong_owner":
        actor = replace(actor, actor_id="worker2")
    else:
        payload["free_slots"] = 3
    denied = case.env.execute("heartbeat", payload, principal=actor)
    assert denied.status == "rejected" and denied.reason_code == reason
    with case.env.engine.connect() as connection:
        row = connection.execute(text("SELECT revision,worker_id,expires_at FROM registry.replicas WHERE tenant_id=:tenant AND project_id=:project"),
            {"tenant": case.env.scope.tenant_id, "project": case.env.scope.project_id}).mappings().one()
    assert row["revision"] == 1 and row["worker_id"] == "worker" and row["expires_at"] == first.heartbeat.expires_at


def test_expiry_changes_only_capacity_and_replaying_heartbeat_does_not_extend_it(installed):
    case = installed
    payload = {"deployment_id": "d1", "replica_id": "r1", "expected_revision": 0, "free_slots": 1, "ttl_seconds": 1}
    first = case.env.execute("heartbeat", payload, principal=case.env.worker, command_id="heartbeat")
    initial = case.env.execute("resolve", case.need)
    assert initial.decision.status == "candidate"
    with case.env.engine.connect() as connection:
        connection.execute(text("SELECT pg_sleep(1.1)"))
    assert case.env.execute("heartbeat", payload, principal=case.env.worker, command_id="heartbeat") == first
    expired = case.env.execute("resolve", case.need)
    assert expired.decision.status == "rejected"
    assert expired.decision.observations.scientific == initial.decision.observations.scientific
    assert expired.decision.observations.capacity.reason_codes == ("no_healthy_replicas",)
    assert case.heartbeat(expected_revision=1).heartbeat.revision == 2
    assert case.env.execute("resolve", case.need).decision.status == "candidate"


@pytest.mark.parametrize("fault,reason", [("duplicate", "duplicate_worker"), ("changed", "immutable_deployment_conflict"),
    ("missing", "deployment_not_found")])
def test_invalid_inventory_requests_are_terminal_and_replayable(installed, fault, reason):
    case = installed
    payload = copy.deepcopy(case.deployment)
    action = "deploy"
    if fault == "duplicate":
        payload["workers"] = ["worker", "worker"]
    elif fault == "changed":
        payload["workers"] = ["worker"]
    else:
        action, payload = "drain_deployment", {"deployment_id": "absent", "expected_revision": 1}
    first = case.env.execute(action, payload, command_id="invalid-inventory")
    assert first.reason_code == reason
    assert case.env.execute(action, payload, command_id="invalid-inventory") == first


@pytest.mark.parametrize("fault", ["effect", "evidence", "context"])
def test_registered_metadata_does_not_grant_scientific_activation(installed, fault):
    case = installed
    raw = copy.deepcopy(case.env.fixture["descriptor"])
    raw["tool"]["binding"]["release"] = "0.2.0"
    if fault == "effect":
        raw["tool"]["side_effects"] = "external"
    elif fault == "evidence":
        raw["authority_ceiling"] = "evidence_proposal"
    else:
        raw["tool"]["applicability"] = ["biological-research"]
    registered, lock = case.register(raw)
    assert registered.status == "accepted" and registered.release.status == "registered"
    assert case.env.execute("activate", {"release": lock, "expected_revision": 1}).reason_code == "activation_profile_denied"
    assert case.env.registry.read_release(case.env.admin, lock["descriptor_sha256"]).revision == 1


def test_revision_exhaustion_fails_closed():
    with pytest.raises(RegistryDenied, match="revision_exhausted"):
        Lifecycle("active", 9007199254740991).changed("drain", 9007199254740991)
