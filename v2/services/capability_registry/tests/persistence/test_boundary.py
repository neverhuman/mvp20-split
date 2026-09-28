"""Real owner transactions prove immutable releases and durable replay boundaries."""

import copy
import json

import pytest
from amphora_capability_registry.catalog.model import RegistryDenied
from amphora_capability_registry.descriptors.identity import ReleaseDocument
from amphora_contracts_tools import ReleaseDescriptor, parse_registry_command
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def registration(env, descriptor=None):
    descriptor = descriptor or env.fixture["descriptor"]
    lock = ReleaseDocument.from_descriptor(ReleaseDescriptor.model_validate_json(json.dumps(descriptor))).to_lock()
    return {"scope": env.scope.model_dump(), "descriptor": descriptor, "expected_lock": lock.model_dump(mode="json")}


def count(env, table):
    assert table in {"commands", "releases", "audit_events", "release_states"}
    with env.engine.connect() as connection:
        return connection.execute(text(f"SELECT count(*) FROM registry.{table} WHERE tenant_id=:tenant AND project_id=:project"),
            {"tenant": env.scope.tenant_id, "project": env.scope.project_id}).scalar_one()


def test_registration_is_immutable_and_receipt_is_original_after_activation(registry_env):
    env = registry_env
    payload = registration(env)
    first = env.execute("register", payload, command_id="original")
    assert first.status == "accepted" and first.release.status == "registered"
    assert first.release.revision == 1 and first.release.lock.model_dump(mode="json") == env.fixture["lock"]
    second = env.execute("register", payload)
    assert second.reason_code == "existing" and second.release == first.release
    activated = env.execute("activate", {"release": payload["expected_lock"], "expected_revision": 1})
    assert activated.release.status == "active" and activated.release.revision == 2
    assert env.execute("register", payload, command_id="original") == first
    assert count(env, "releases") == count(env, "release_states") == 1
    assert count(env, "commands") == count(env, "audit_events") == 3
    read = env.registry.read_release(env.admin, first.release.lock.descriptor_sha256)
    assert read.status == "active" and read.descriptor == first.release.descriptor


def test_same_key_different_bytes_is_terminal_conflict_and_command_change_cannot_mutate(registry_env):
    env = registry_env
    payload = registration(env)
    original = env.execute("register", payload, command_id="register")
    changed = copy.deepcopy(payload["descriptor"])
    changed["tool"]["purpose"] = "Different declared function"
    request = registration(env, changed)
    denied = env.execute("register", request, command_id="conflict")
    assert denied.status == "rejected" and denied.reason_code == "immutable_release_conflict"
    assert env.execute("register", request, command_id="conflict") == denied
    with pytest.raises(RegistryDenied, match="command_identity_conflict"):
        env.execute("register", request, command_id="register")
    assert count(env, "releases") == 1 and count(env, "commands") == 2
    assert env.registry.read_release(env.admin, original.release.lock.descriptor_sha256) == original.release


@pytest.mark.parametrize("denied", [False, True])
def test_post_insert_failure_rolls_back_owner_state(registry_env, monkeypatch, denied):
    env = registry_env

    def fail(*_):
        if denied:
            raise RegistryDenied("injected_denial")
        raise RuntimeError("injected_failure")

    monkeypatch.setattr("amphora_capability_registry.catalog.releases.read_release", fail)
    if denied:
        assert env.execute("register", registration(env)).reason_code == "injected_denial"
    else:
        with pytest.raises(RuntimeError, match="injected_failure"):
            env.execute("register", registration(env))
    assert count(env, "releases") == count(env, "release_states") == 0
    assert count(env, "commands") == count(env, "audit_events") == int(denied)


def test_identity_and_action_denial_write_nothing(registry_env):
    env = registry_env
    command = parse_registry_command("registry.register", env.raw("register", registration(env)))
    for principal in (env.other, env.worker):
        with pytest.raises(RegistryDenied):
            env.registry.execute(principal, command)
    assert count(env, "commands") == count(env, "releases") == 0


@pytest.mark.parametrize("statement", ["UPDATE registry.releases SET descriptor=descriptor", "DELETE FROM registry.releases",
    "UPDATE registry.commands SET receipt=receipt", "DELETE FROM registry.audit_events", "SELECT * FROM runtime.commands",
    "SELECT * FROM artifacts.commands", "CREATE TABLE registry.forbidden(id int)"])
def test_service_role_cannot_rewrite_history_or_access_peer_state(registry_env, statement):
    with pytest.raises(DBAPIError) as error, registry_env.engine.begin() as connection:
        connection.execute(text(statement))
    assert getattr(error.value.orig, "sqlstate", None) == "42501"
