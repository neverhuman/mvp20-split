"""Real PostgreSQL synthetic admission; no worker dispatch or graph execution."""

import copy
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials, RuntimePrincipal
from amphora_campaign_runtime.lifecycle.admission import FixtureAdmission, FixtureCatalog
from amphora_campaign_runtime.persistence.commands import CommandConflict
from amphora_campaign_runtime.persistence.migrate import upgrade
from amphora_contracts_core import Scope
from amphora_contracts_runtime import AdmitFixtureRun, parse_command
from fastapi.testclient import TestClient
from postgres_fixture import owned_state
from sqlalchemy import URL, create_engine, event, text

pytestmark = [pytest.mark.postgres, pytest.mark.skipif(os.environ.get("AMPHORA_TEST_POSTGRES") != "1",
                                                     reason="Explicit PostgreSQL opt-in required")]


@pytest.fixture
def fixture_env():
    state = owned_state()
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="runtime_migrator", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    upgrade(url.render_as_string(hide_password=False))
    engine = create_engine(url.set(username="runtime_service"), connect_args={"options": "-c statement_timeout=5000"})
    scope = Scope(tenant_id="admission-tests", project_id=uuid.uuid4().hex)
    raw = json.loads((Path(__file__).parents[1] / "fixtures/prepared-run.json").read_text())
    raw["identity"]["scope"] = scope.model_dump()
    for invocation in raw["payload"]["invocations"]:
        for binding in invocation["inputs"]:
            binding["artifact"]["scope"] = scope.model_dump()
    definition = AdmitFixtureRun.model_validate_json(json.dumps(raw["payload"]))
    service = FixtureAdmission(engine, FixtureCatalog([definition]))
    principal = RuntimePrincipal("worker-1", scope, frozenset({"admit"}))
    credentials = RuntimeCredentials([("x" * 32, principal)])
    try:
        yield SimpleNamespace(engine=engine, service=service, principal=principal, credentials=credentials, raw=raw)
    finally:
        with engine.begin() as conn:
            conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE tenant_id=:tenant AND project_id=:project "
                              "AND status='running'"), {"tenant": scope.tenant_id, "project": scope.project_id})
        engine.dispose()


def command(env, raw=None):
    return parse_command("runtime.admit_fixture", json.dumps(raw or env.raw))


def count(env, table):
    with env.engine.connect() as conn:
        return conn.execute(text("SELECT count(*) FROM runtime." + table +
            " WHERE tenant_id=:tenant AND project_id=:project"),
            {"tenant": env.principal.scope.tenant_id, "project": env.principal.scope.project_id}).scalar_one()


def test_admission_replay_and_conflicting_bytes(fixture_env):
    e = fixture_env
    receipt = e.service.admit(e.principal, command(e))
    assert receipt.outcome.status == "accepted"
    assert e.service.admit(e.principal, command(e)) == receipt
    assert count(e, "runs") == count(e, "activations") == count(e, "audit_events") == 1
    changed = copy.deepcopy(e.raw)
    changed["payload"]["budget"]["limit"] += 1
    with pytest.raises(CommandConflict):
        e.service.admit(e.principal, command(e, changed))


@pytest.mark.parametrize("field", ["tool", "input", "budget", "plan", "fixture"])
def test_exact_fixture_pins_reject_changes(fixture_env, field):
    e = fixture_env
    raw = copy.deepcopy(e.raw)
    if field == "tool":
        raw["payload"]["invocations"][0]["tool"]["image_sha256"] = "d" * 64
    elif field == "input":
        raw["payload"]["invocations"][0]["inputs"][0]["artifact"]["artifact_id"] = "changed"
    elif field == "budget":
        raw["payload"]["budget"]["limit"] += 1
    elif field == "plan":
        raw["payload"]["plan_sha256"] = "d" * 64
    else:
        raw["payload"]["fixture_id"] = "unknown"
    receipt = e.service.admit(e.principal, command(e, raw))
    assert receipt.outcome.status == "rejected"
    assert count(e, "runs") == 0
    assert e.service.admit(e.principal, command(e, raw)) == receipt


def test_two_concurrent_admissions_allow_only_one(fixture_env):
    e = fixture_env
    barrier = Barrier(2)

    def admit(_):
        raw = copy.deepcopy(e.raw)
        raw["identity"]["command_id"] = uuid.uuid4().hex
        barrier.wait(timeout=10)
        return e.service.admit(e.principal, command(e, raw))

    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(admit, range(2)))
    assert sorted(r.outcome.status for r in receipts) == ["accepted", "rejected"]
    assert next(r for r in receipts if r.outcome.status == "rejected").outcome.reason_code == "active_run_exists"
    assert count(e, "runs") == 1


def test_receipt_fault_rolls_back_run_activation_and_audit(fixture_env):
    e = fixture_env

    def fault(_conn, _cursor, statement, *_args):
        if statement.startswith("UPDATE runtime.commands SET status="):
            raise RuntimeError("injected receipt fault")

    event.listen(e.engine, "after_cursor_execute", fault)
    try:
        with pytest.raises(RuntimeError, match="injected"):
            e.service.admit(e.principal, command(e))
    finally:
        event.remove(e.engine, "after_cursor_execute", fault)
    assert count(e, "runs") == count(e, "activations") == count(e, "audit_events") == 0
    assert e.service.admit(e.principal, command(e)).outcome.status == "accepted"


def test_http_authentication_and_non_executable_general_graph(fixture_env):
    e = fixture_env
    with TestClient(create_app(e.service, e.credentials)) as client:
        assert client.post("/v1/fixture-runs", json=e.raw).status_code == 401
        assert client.get("/health").json()["execution_available"] is False
        wrong = copy.deepcopy(e.raw)
        wrong["identity"]["actor_id"] = "impostor"
        headers = {"Authorization": "Bearer " + "x" * 32}
        assert client.post("/v1/fixture-runs", json=wrong, headers=headers).status_code == 403
        reply = client.post("/v1/fixture-runs", json=e.raw, headers=headers)
        assert reply.status_code == 200 and reply.json()["outcome"]["status"] == "accepted"
