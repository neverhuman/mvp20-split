"""Real PostgreSQL synthetic admission; no worker dispatch or graph execution."""

import json
import os
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials, RuntimePrincipal
from amphora_campaign_runtime.lifecycle.admission import FixtureAdmission, FixtureCatalog
from amphora_campaign_runtime.persistence.migrate import upgrade
from amphora_contracts_core import Scope
from amphora_contracts_runtime import AdmitFixtureRun
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
    raw = json.loads((Path(__file__).parents[1] / "fixtures/prepared-run.json").read_text())
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

