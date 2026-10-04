import json
import os
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.persistence.journal import PlanningJournal
from amphora_agent_planning.persistence.migrate import upgrade
from amphora_contracts_core import Scope
from amphora_contracts_planning import reference_proposal_schema
from sqlalchemy import URL, create_engine
from sqlalchemy.engine import make_url


@pytest.fixture(scope="session")
def planning_database():
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        pytest.skip("Explicit PostgreSQL fixture opt-in required")
    migrator = os.environ.get("AMPHORA_TEST_PLANNING_MIGRATOR_URL")
    service = os.environ.get("AMPHORA_TEST_PLANNING_SERVICE_URL")
    if migrator or service:
        assert migrator and service, "Both independently scoped Planning URLs are required"
        upgrade(migrator)
        upgrade(migrator)
        return make_url(service)
    from postgres_fixture import owned_state, planning_owner

    state = owned_state()
    planning_owner(state)
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="planning_migrator", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    upgrade(url.render_as_string(hide_password=False))
    upgrade(url.render_as_string(hide_password=False))
    return url.set(username="planning_service")


@pytest.fixture
def stored(planning_database):
    raw = json.loads((Path(__file__).parents[1] / "context/fixtures/request.json").read_bytes())
    scope = Scope(tenant_id="planning-storage", project_id=uuid.uuid4().hex)
    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {"tenant_id", "project_id"}:
                value.update(scope.model_dump())
            for child in value.values():
                rescope(child)
        elif isinstance(value, list):
            for child in value:
                rescope(child)
    rescope(raw)
    raw["context"]["output_schema"] = reference_proposal_schema().model_dump(mode="json")
    snapshot = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id="fixture", scope=scope)
    principal = Principal("fixture", scope, frozenset({"record_requests", "record_attempts", "read_attempts"}))
    engine = create_engine(planning_database, connect_args={"options": "-c statement_timeout=5000"})
    yield SimpleNamespace(journal=PlanningJournal(engine), engine=engine, principal=principal, snapshot=snapshot,
                          first=AttemptBinding(snapshot, 1), second=AttemptBinding(snapshot, 2))
    engine.dispose()
