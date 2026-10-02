import json
import os
import subprocess
import sys

import pytest
from amphora_knowledge.access import Principal
from amphora_knowledge.transport.credentials import Credentials
from amphora_knowledge.transport.host import KnowledgeHost
from fastapi.testclient import TestClient


@pytest.fixture
def configuration(graph_fixture, monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_TEST_TOKEN", "k"*32)
    return {"database_url_env": "KNOWLEDGE_TEST_DATABASE", "principals": [{"token_env": "KNOWLEDGE_TEST_TOKEN",
        "actor_id": "host-reader", "scope": graph_fixture.proposal.graph.scope.model_dump(), "actions": ["read_graph"]}],
        "vocabulary": graph_fixture.vocabulary.record.model_dump(mode="json"), "policy": graph_fixture.policy.definition(),
        "data": {"endpoint": "http://127.0.0.1:1", "token_env": "KNOWLEDGE_TEST_TOKEN"},
        "research": {"endpoint": "http://127.0.0.1:1", "token_env": "KNOWLEDGE_TEST_TOKEN"}}


@pytest.mark.postgres
def test_host_reads_profile_without_peer_connections(configuration, knowledge_database, monkeypatch, tmp_path):
    monkeypatch.setenv("KNOWLEDGE_TEST_DATABASE", knowledge_database.render_as_string(hide_password=False))
    host = KnowledgeHost.configured(configuration)
    try:
        with TestClient(host.app) as client:
            assert client.get("/health").json()["authority"] == "structural_only"
            graph = {"scope": configuration["principals"][0]["scope"], "graph_id": "host-profile"}
            response = client.post("/v1/graph-profiles/read", json=graph, headers={"Authorization": "Bearer " + "k"*32})
            assert response.status_code == 200 and response.json()["origin"] == "configured_default"
    finally:
        host.close()
    path = tmp_path / "host.json"
    path.write_text(json.dumps(configuration), encoding="utf-8")
    result = subprocess.run([sys.executable, "-I", "-m", "amphora_knowledge", "check", "--config", str(path)],
        env=dict(os.environ), capture_output=True, timeout=20)
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"status": "ready", "authority": "structural_only"}


@pytest.mark.postgres
def test_migration_role_cannot_host(configuration, knowledge_database, monkeypatch):
    monkeypatch.setenv("KNOWLEDGE_TEST_DATABASE", knowledge_database.set(username="knowledge_migrator").render_as_string(hide_password=False))
    with pytest.raises(ValueError, match="knowledge_service_role_required"):
        KnowledgeHost.configured(configuration)


@pytest.mark.parametrize("mutation", [
    lambda c: c.update(unexpected=True), lambda c: c.update(principals=[]),
    lambda c: c["principals"][0].update(actions=["accept"]),
    lambda c: c["principals"][0].update(actor_id="invalid actor"),
    lambda c: c["principals"][0].update(token_env="missing"),
    lambda c: c["data"].update(endpoint="http://example.org:8080"),
    lambda c: c["policy"].update(authority="scientific"),
    lambda c: c.update(reasoning=None),
    lambda c: c.update(reasoning={}),
    lambda c: c.update(publication=None),
    lambda c: c.update(publication={"actor_id": "bad actor", "issuer_id": "issuer", "token_env": "KNOWLEDGE_TEST_TOKEN"}),
    lambda c: c.update(publication={"actor_id": "publisher", "issuer_id": "issuer", "token_env": "missing"}),
], ids=["extra", "empty", "action", "actor", "secret", "endpoint", "authority", "reasoning-null", "reasoning-object",
        "publication-null", "publication-actor", "publication-secret"])
def test_invalid_configuration_fails_before_connecting(configuration, mutation):
    mutation(configuration)
    with pytest.raises(ValueError):
        KnowledgeHost.configured(configuration)


def test_credentials_never_store_plaintext_and_reject_duplicate(graph_fixture):
    principal = Principal("reader", graph_fixture.proposal.graph.scope, frozenset({"read_graph"}))
    token = "k"*32
    credentials = Credentials([(token, principal)])
    assert token not in repr(credentials.__dict__)
    assert credentials.authenticate("Bearer " + token) == principal
    for header in [None, "Basic x", "Bearer " + "x"*32, "Bearer \u00ff", "Bearer " + "x"*513]:
        with pytest.raises(ValueError, match="unauthorized"):
            credentials.authenticate(header)
    with pytest.raises(ValueError, match="duplicate"):
        Credentials([(token, principal), (token, principal)])
