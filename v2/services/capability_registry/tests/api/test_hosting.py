"""Explicit host configuration and owner-role checks against real PostgreSQL."""

import json

import pytest
from amphora_capability_registry.hosting import Host, HostConfig
from pydantic import ValidationError


def config(scope):
    return {"database_url_env": "REGISTRY_TEST_DATABASE", "principals": [{"actor_id": "admin", "scope": scope,
        "token_env": "REGISTRY_TEST_TOKEN", "actions": ["read"]}], "resources": {"architecture": "x86_64",
        "operating_system": "windows", "cpu_millicores": 2000, "memory_mib": 1024, "gpu_count": 0,
        "timeout_seconds": 300, "max_parallel_invocations": 8, "max_batch_size": 128}}


@pytest.mark.parametrize("fault", ["fault_hook", "floating_action", "naive_resource", "inline_secret"])
def test_normal_host_config_rejects_test_hooks_and_unknown_authority(fault):
    value = config({"tenant_id": "test", "project_id": "test"})
    if fault == "fault_hook":
        value["fault"] = "after_commit"
    elif fault == "floating_action":
        value["principals"][0]["actions"] = ["*"]
    elif fault == "naive_resource":
        value["resources"]["memory_mib"] = True
    else:
        value["database_url"] = "postgresql://not-allowed"
    with pytest.raises(ValidationError):
        HostConfig.model_validate_json(json.dumps(value))


@pytest.mark.postgres
def test_host_load_is_explicit_service_role_and_read_only(registry_env, tmp_path, monkeypatch):
    value = config(registry_env.scope.model_dump())
    path = tmp_path/"registry.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setenv("REGISTRY_TEST_DATABASE", registry_env.engine.url.render_as_string(hide_password=False))
    monkeypatch.setenv("REGISTRY_TEST_TOKEN", "a"*32)
    host = Host.load(path)
    try:
        assert "/v1/registry/{operation}" in host.app().openapi()["paths"]
    finally:
        host.close()
    monkeypatch.setenv("REGISTRY_TEST_DATABASE", registry_env.engine.url.set(username="registry_migrator").render_as_string(hide_password=False))
    with pytest.raises(ValueError, match="service role"):
        Host.load(path)
