"""Scoped consistent observations and explicit service-role startup."""

import json
import uuid
from dataclasses import replace

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.hosting import Host
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.lifecycle.reads import RuntimeReads
from amphora_contracts_core import Scope
from amphora_contracts_runtime import parse_command
from fastapi.testclient import TestClient


def command(e, family, payload):
    return parse_command(family, json.dumps({"identity": {"command_family": family,
        "command_id": uuid.uuid4().hex, "actor_id": e.principal.actor_id,
        "scope": e.principal.scope.model_dump()}, "payload": payload}))


def test_read_projection_tracks_current_fence_and_renewal(fixture_env):
    e = fixture_env
    principal = replace(e.principal, actions=e.principal.actions | {"read"})
    run = e.service.admit(e.principal, command(e, "runtime.admit_fixture", e.raw["payload"])).outcome.committed.object_id
    reader = RuntimeReads(e.engine)
    before = reader.run(principal, run)
    assert before.activations[0].latest_attempt is None
    first = RuntimeLeases(e.engine).claim(e.principal, command(e, "runtime.claim", {
        "run_id": run, "worker_id": e.principal.actor_id, "tool": e.raw["payload"]["invocations"][0]["tool"]})).outcome.invocation
    with TestClient(create_app(e.service, RuntimeCredentials([("x" * 32, principal)]))) as client:
        headers = {"Authorization": "Bearer " + "x" * 32}
        renew = command(e, "runtime.renew", {"attempt": {"run_id": run, "invocation_id": first.invocation_id,
            "attempt_id": first.attempt_id, "fence": first.fence}, "lease_seconds": 20})
        response = client.post("/v1/attempts/renew", headers=headers, content=renew.canonical_bytes)
        assert response.status_code == 200
        data = client.get(f"/v1/runs/{run}", headers=headers).json()
        assert data["budget"] == {"limit": 5, "available": 4, "reserved": 1, "spent": 0}
        assert data["activations"][0]["latest_attempt"]["attempt_id"] == first.attempt_id
        assert data["revision"] > before.revision
        assert client.get("/ready").status_code == 200
    with pytest.raises(TransitionError, match="access_denied"):
        reader.run(e.principal, run)
    other = replace(principal, scope=Scope(tenant_id=principal.scope.tenant_id, project_id="other"))
    with pytest.raises(TransitionError, match="run_unavailable"):
        reader.run(other, run)


def config(e, tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_RUNTIME_URL", e.engine.url.render_as_string(hide_password=False))
    monkeypatch.setenv("TEST_RUNTIME_TOKEN", "x" * 32)
    value = {"database_url_env": "TEST_RUNTIME_URL", "principals": [
        {"token_env": "TEST_RUNTIME_TOKEN", "actor_id": e.principal.actor_id,
         "scope": e.principal.scope.model_dump(), "actions": ["admit", "claim", "renew", "read"]}],
        "fixtures": [e.raw["payload"]]}
    path = tmp_path / "host.json"
    path.write_text(json.dumps(value))
    return path, value


def test_host_requires_correct_role_and_explicit_configuration(fixture_env, tmp_path, monkeypatch):
    e = fixture_env
    path, raw = config(e, tmp_path, monkeypatch)
    host = Host.load(path)
    try:
        assert "/v1/runs/{run_id}" in host.app().openapi()["paths"]
    finally:
        host.close()
    monkeypatch.setenv("TEST_RUNTIME_URL", e.engine.url.set(username="runtime_migrator").render_as_string(hide_password=False))
    with pytest.raises(ValueError, match="service role"):
        Host.load(path)
    raw["principals"][0]["actions"] = ["arbitrary"]
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="configured action"):
        Host.load(path)


def test_host_rejects_duplicate_identity_and_empty_allowlist(fixture_env, tmp_path, monkeypatch):
    path, raw = config(fixture_env, tmp_path, monkeypatch)
    raw["principals"].append(raw["principals"][0])
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="Duplicate"):
        Host.load(path)
    raw["principals"].pop()
    raw["fixtures"] = []
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="allowlist"):
        Host.load(path)
