import os
import uuid

import pytest
from amphora_contracts_core import Scope
from amphora_research.persistence.ledger import IdentityLedger
from amphora_research.persistence.migrate import upgrade
from postgres_fixture import owned_state, research_owner
from sqlalchemy import URL, create_engine


@pytest.fixture(scope="session")
def research_database():
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        pytest.skip("Explicit PostgreSQL opt-in required")
    state = owned_state()
    research_owner(state)
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="research_migrator", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    upgrade(url.render_as_string(hide_password=False))
    upgrade(url.render_as_string(hide_password=False))
    return url.set(username="research_service")


@pytest.fixture
def ledger(research_database):
    engine = create_engine(research_database, connect_args={"options": "-c statement_timeout=5000"})
    yield IdentityLedger(engine), Scope(tenant_id="research-tests", project_id=uuid.uuid4().hex)
    engine.dispose()
