import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from amphora_contracts_knowledge import DomainVocabulary, GraphChangeProposal
from amphora_knowledge.authoring.policy import StructuralPolicy
from amphora_knowledge.authoring.state import GraphState
from amphora_knowledge.authoring.vocabulary import Vocabulary


@pytest.fixture
def graph_fixture():
    case = json.loads((Path(__file__).parent / "fixtures/initial.json").read_text(encoding="utf-8"))
    vocabulary = Vocabulary(DomainVocabulary.model_validate_json(json.dumps(case["vocabulary"])))
    policy = StructuralPolicy()
    raw = case["proposal"]
    raw["vocabulary"] = vocabulary.reference.model_dump(mode="json")
    raw["policy"] = policy.reference.model_dump(mode="json")
    proposal = GraphChangeProposal.model_validate_json(json.dumps(raw))
    state = GraphState(proposal.graph, vocabulary, policy)
    return SimpleNamespace(state=state, proposal=proposal, vocabulary=vocabulary, policy=policy)


@pytest.fixture(scope="session")
def knowledge_database():
    import os

    from amphora_knowledge.persistence.migrate import upgrade
    from postgres_fixture import knowledge_owner, owned_state
    from sqlalchemy import URL

    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        pytest.skip("Explicit PostgreSQL opt-in required")
    state = owned_state()
    knowledge_owner(state)
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="knowledge_migrator", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    upgrade(url.render_as_string(hide_password=False))
    upgrade(url.render_as_string(hide_password=False))
    return url.set(username="knowledge_service")


@pytest.fixture
def stored_graph(graph_fixture, knowledge_database):
    import uuid

    from amphora_knowledge.access import Principal
    from amphora_knowledge.persistence.ledger import KnowledgeLedger
    from sqlalchemy import create_engine

    raw = graph_fixture.proposal.model_dump(mode="json")
    project = uuid.uuid4().hex

    def rescope(value):
        if isinstance(value, dict):
            if set(value) == {"tenant_id", "project_id"}:
                value["project_id"] = project
            for item in value.values():
                rescope(item)
        elif isinstance(value, list):
            for item in value:
                rescope(item)

    rescope(raw)
    proposal = GraphChangeProposal.model_validate_json(json.dumps(raw))
    engine = create_engine(knowledge_database, connect_args={"options": "-c statement_timeout=5000"})
    principal = Principal("reviewer", proposal.graph.scope, frozenset({"propose_graph", "read_graph"}))
    ledger = KnowledgeLedger(engine, graph_fixture.vocabulary, graph_fixture.policy)
    yield SimpleNamespace(ledger=ledger, principal=principal, proposal=proposal, engine=engine,
                          vocabulary=graph_fixture.vocabulary, policy=graph_fixture.policy)
    engine.dispose()
