"""HTTP authentication and actual owner persistence; no mock registry peers."""

import pytest

pytestmark = pytest.mark.postgres


def payload(env):
    return {"scope": env.scope.model_dump(), "descriptor": env.fixture["descriptor"], "expected_lock": env.fixture["lock"]}


def test_http_registration_read_replay_scope_and_revision(registry_env):
    env = registry_env
    body = env.raw("register", payload(env), command_id="http-registration")
    path = "/v1/registry/register"
    response = env.client.post(path, content=body, headers=env.headers)
    assert response.status_code == 200
    original = response.json()
    assert original["status"] == "accepted"
    assert env.client.post(path, content=body, headers=env.headers).json() == original
    digest = original["release"]["lock"]["descriptor_sha256"]
    assert env.client.get("/v1/releases/"+digest, headers=env.headers).json() == original["release"]
    assert env.client.get("/v1/releases/"+digest, headers={"Authorization": "Bearer "+"b"*32}).status_code == 404
    assert env.client.post(path, content=body).status_code == 401
    assert env.client.post(path, content=body, headers={"Authorization": "Bearer "+"b"*32}).status_code == 403
    activate = env.raw("activate", {"release": env.fixture["lock"], "expected_revision": 2})
    rejected = env.client.post("/v1/registry/activate", content=activate, headers=env.headers)
    assert rejected.json()["reason_code"] == "revision_conflict"


@pytest.mark.parametrize("body,reason", [(b'{"identity":{},"identity":{},"payload":{}}', "duplicate_key"),
    (b"x"*262145, "too_large"), (b"{", "invalid_json")], ids=["duplicate-key", "oversized-body", "malformed-json"])
def test_http_parse_failures_are_bounded_reason_codes(registry_env, body, reason):
    response = registry_env.client.post("/v1/registry/register", content=body, headers=registry_env.headers)
    assert response.status_code == 422 and response.json() == {"reason_code": reason}


def test_deployment_heartbeat_resolution_and_drain_keep_original_pins(registry_env):
    env = registry_env

    def call(action, value, actor="admin"):
        headers = env.headers if actor == "admin" else {"Authorization": "Bearer "+"w"*32}
        response = env.client.post("/v1/registry/"+action, content=env.raw(action, value, actor), headers=headers)
        assert response.status_code == 200
        return response.json()

    assert call("register", payload(env))["reason_code"] == "registered"
    lock = env.fixture["lock"]
    assert call("activate", {"release": lock, "expected_revision": 1})["release"]["status"] == "active"
    deployment = {"deployment_id": "d1", "release": lock, "architecture": "x86_64", "operating_system": "windows", "workers": ["worker"]}
    assert call("deploy", deployment)["deployment"]["revision"] == 1
    observed = call("heartbeat", {"deployment_id": "d1", "replica_id": "r1", "expected_revision": 0, "free_slots": 1, "ttl_seconds": 30}, "worker")
    assert observed["heartbeat"]["revision"] == 1
    tool = env.fixture["descriptor"]["tool"]
    request = {"release": lock, "context": "synthetic-tests", "inputs": tool["inputs"], "outputs": tool["outputs"]}
    resolved = call("resolve", request)
    assert resolved["decision"]["status"] == "candidate" and resolved["release"]["lock"] == lock
    assert env.client.get("/v1/deployments/d1", headers=env.headers).json()["deployment"] == deployment
    assert call("drain", {"release": lock, "expected_revision": 2})["release"]["revision"] == 3
    assert call("resolve", request)["reason_code"] == "release_not_active"
    assert call("revoke", {"release": lock, "expected_revision": 3})["release"]["lock"] == lock
