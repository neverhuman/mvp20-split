"""Owner-local synthetic installation builders for policy tests."""

import copy
import json
from types import SimpleNamespace

import pytest
from amphora_capability_registry.descriptors.identity import ReleaseDocument
from amphora_contracts_tools import ReleaseDescriptor


@pytest.fixture
def installed(registry_env):
    env = registry_env

    def register(raw=None):
        raw = raw or copy.deepcopy(env.fixture["descriptor"])
        descriptor = ReleaseDescriptor.model_validate_json(json.dumps(raw))
        lock = ReleaseDocument.from_descriptor(descriptor).to_lock().model_dump(mode="json")
        result = env.execute("register", {"scope": env.scope.model_dump(), "descriptor": raw, "expected_lock": lock})
        return result, lock

    registered, lock = register()
    assert registered.status == "accepted"
    assert env.execute("activate", {"release": lock, "expected_revision": 1}).status == "accepted"
    deployment = {"deployment_id": "d1", "release": lock, "architecture": "x86_64", "operating_system": "windows", "workers": ["worker", "worker2"]}
    assert env.execute("deploy", deployment).status == "accepted"
    tool = env.fixture["descriptor"]["tool"]
    need = {"release": lock, "context": "synthetic-tests", "inputs": tool["inputs"], "outputs": tool["outputs"]}

    def heartbeat(**changes):
        payload = {"deployment_id": "d1", "replica_id": "r1", "expected_revision": 0, "free_slots": 1, "ttl_seconds": 30}
        payload.update(changes)
        return env.execute("heartbeat", payload, principal=env.worker)

    return SimpleNamespace(env=env, register=register, lock=lock, deployment=deployment, need=need, heartbeat=heartbeat)
