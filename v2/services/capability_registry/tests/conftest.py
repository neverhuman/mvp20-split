"""Registry-owned real PostgreSQL fixtures; no peer implementation imports."""

import json
import os
import uuid
from types import SimpleNamespace

import pytest
from amphora_capability_registry.access import Credentials
from amphora_capability_registry.api import create_app
from amphora_capability_registry.catalog.model import Principal
from amphora_capability_registry.catalog.service import Registry
from amphora_capability_registry.descriptors.policy import PermissionPolicy
from amphora_capability_registry.descriptors.requirements import ResourceAllowance
from amphora_capability_registry.persistence.migrate import upgrade
from amphora_contracts_core import Scope
from amphora_contracts_tools import parse_registry_command
from export_schemas import ROOT
from fastapi.testclient import TestClient
from postgres_fixture import owned_state, registry_owner
from sqlalchemy import URL, create_engine


@pytest.fixture(scope="session")
def registry_database():
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        pytest.skip("Explicit PostgreSQL opt-in required")
    state = owned_state()
    registry_owner(state)
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="registry_migrator", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    upgrade(url.render_as_string(hide_password=False))
    upgrade(url.render_as_string(hide_password=False))
    return url.set(username="registry_service")


@pytest.fixture
def registry_env(registry_database):
    scope = Scope(tenant_id="registry-tests", project_id=uuid.uuid4().hex)
    actions = frozenset({"register", "activate", "drain", "revoke", "read", "deploy", "drain_deployment", "revoke_deployment", "resolve"})
    admin = Principal("admin", scope, actions)
    worker = Principal("worker", scope, frozenset({"heartbeat"}))
    other = Principal("admin", Scope(tenant_id="other", project_id="other"), actions)
    engine = create_engine(registry_database, connect_args={"options": "-c statement_timeout=5000"})
    registry = Registry(engine, ResourceAllowance("x86_64", "windows", 2000, 1024, 0, 300, 8, 128), PermissionPolicy())
    fixture = json.loads((ROOT / "contracts/fixtures/v1/tool_releases.json").read_text())[0]

    def raw(action, payload, actor="admin", command_id=None):
        return json.dumps({"identity": {"scope": scope.model_dump(), "actor_id": actor,
            "command_family": "registry."+action, "command_id": command_id or uuid.uuid4().hex}, "payload": payload})

    def execute(action, payload, principal=admin, command_id=None):
        return registry.execute(principal, parse_registry_command("registry."+action, raw(action, payload, principal.actor_id, command_id)))

    credentials = Credentials([("a"*32, admin), ("w"*32, worker), ("b"*32, other)])
    with TestClient(create_app(registry, credentials)) as client:
        yield SimpleNamespace(scope=scope, admin=admin, worker=worker, other=other, engine=engine, registry=registry,
            fixture=fixture, raw=raw, execute=execute, client=client, headers={"Authorization": "Bearer "+"a"*32})
    engine.dispose()
