"""Runtime-owned reusable PostgreSQL fixture; synthetic lifecycle only."""

import copy
import json
import os
import uuid
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials, RuntimePrincipal
from amphora_campaign_runtime.lifecycle.admission import FixtureAdmission, FixtureCatalog
from amphora_campaign_runtime.lifecycle.claims import RuntimeLeases
from amphora_campaign_runtime.persistence.migrate import upgrade
from amphora_contracts_core import Scope
from amphora_contracts_runtime import AdmitFixtureRun, parse_command
from amphora_contracts_tools import ToolDescriptor
from postgres_fixture import owned_state
from sqlalchemy import URL, create_engine, text


@pytest.fixture
def fixture_env():
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        pytest.skip("Explicit PostgreSQL opt-in required")
    state = owned_state()
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="runtime_migrator", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    upgrade(url.render_as_string(hide_password=False))
    engine = create_engine(url.set(username="runtime_service"), connect_args={"options": "-c statement_timeout=5000"})
    scope = Scope(tenant_id="admission-tests", project_id=uuid.uuid4().hex)
    raw = json.loads((Path(__file__).parent / "fixtures/prepared-run.json").read_text())
    raw["identity"]["scope"] = scope.model_dump()
    for invocation in raw["payload"]["invocations"]:
        for binding in invocation["inputs"]:
            binding["artifact"]["scope"] = scope.model_dump()
    definition = AdmitFixtureRun.model_validate_json(json.dumps(raw["payload"]))
    service = FixtureAdmission(engine, FixtureCatalog([definition]))
    principal = RuntimePrincipal("worker-1", scope, frozenset({"admit", "claim", "renew"}))
    credentials = RuntimeCredentials([("x" * 32, principal)])
    try:
        yield SimpleNamespace(engine=engine, service=service, principal=principal, credentials=credentials, raw=raw)
    finally:
        with engine.begin() as conn:
            conn.execute(text("UPDATE runtime.runs SET status='cancelled' WHERE tenant_id=:tenant AND project_id=:project "
                              "AND status='running'"), {"tenant": scope.tenant_id, "project": scope.project_id})
        engine.dispose()


@pytest.fixture
def completion_env(fixture_env, request):
    e = fixture_env
    e.principal = replace(e.principal, actions=e.principal.actions | {"complete", "cancel", "revoke", "read"})
    e.raw["payload"]["invocations"][0]["timeout_seconds"] = 120
    spec = e.raw["payload"]["invocations"][0]
    if getattr(request, "param", 1) == 2:
        second = copy.deepcopy(spec)
        second.update(activation_id="iteration-1.n2", invocation_id="i2", node_id="n2")
        e.raw["payload"]["invocations"].append(second)
    schema = spec["inputs"][0]["artifact"]["schema_ref"]
    port = {"name": "value", "schema_ref": schema, "representation": "synthetic", "unit": "1"}
    descriptor = ToolDescriptor.model_validate_json(json.dumps({"schema_version": "1", "binding": spec["tool"],
        "purpose": "Synthetic lifecycle acceptance only", "applicability": ["test"],
        "inputs": [port], "outputs": [port], "side_effects": "pure", "checkpoint_schema": schema}))
    e.service = FixtureAdmission(e.engine, FixtureCatalog(
        [AdmitFixtureRun.model_validate_json(json.dumps(e.raw["payload"]))], [descriptor]))

    def command(family, payload, identity=None):
        return parse_command(family, json.dumps({"identity": {"command_family": family,
            "command_id": identity or uuid.uuid4().hex, "actor_id": e.principal.actor_id,
            "scope": e.principal.scope.model_dump()}, "payload": payload}))
    run = e.service.admit(e.principal, command("runtime.admit_fixture", e.raw["payload"])).outcome.committed.object_id
    claim_command = command("runtime.claim", {
        "run_id": run, "worker_id": e.principal.actor_id, "tool": spec["tool"], "lease_seconds": 90})
    invocation = RuntimeLeases(e.engine).claim(e.principal, claim_command).outcome.invocation
    artifact = {**spec["inputs"][0]["artifact"], "artifact_id": "synthetic-output"}
    payload = {"run_id": run, "completion": {"schema_version": "1", "invocation_id": invocation.invocation_id,
        "attempt_id": invocation.attempt_id, "fence": invocation.fence,
        "outcome": {"status": "succeeded", "outputs": [{"port": "value", "artifact": artifact}]}}}
    return SimpleNamespace(env=e, run=run, invocation=invocation, command=command, payload=payload, descriptor=descriptor, claim_command=claim_command)
