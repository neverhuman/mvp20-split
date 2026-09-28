"""Real PostgreSQL synthetic admission; no worker dispatch or graph execution."""

import copy
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.persistence.commands import CommandConflict
from amphora_contracts_runtime import parse_command
from fastapi.testclient import TestClient
from sqlalchemy import event, text

pytestmark = [pytest.mark.postgres, pytest.mark.skipif(os.environ.get("AMPHORA_TEST_POSTGRES") != "1",
                                                     reason="Explicit PostgreSQL opt-in required")]




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
