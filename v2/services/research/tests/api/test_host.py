import pytest
from amphora_contracts_core import Scope
from amphora_research.transport.host import ResearchHost
from fastapi.testclient import TestClient


def configuration():
    return {"database_url_env": "RESEARCH_TEST_URL", "principals": [{"token_env": "RESEARCH_TEST_TOKEN",
        "actor_id": "reader", "scope": {"tenant_id": "host-tests", "project_id": "synthetic"},
        "actions": ["resolve_identity"]}]}


def test_configured_host_uses_service_role_and_scoped_resolution(research_database, monkeypatch):
    monkeypatch.setenv("RESEARCH_TEST_URL", research_database.render_as_string(hide_password=False))
    monkeypatch.setenv("RESEARCH_TEST_TOKEN", "c" * 32)
    host = ResearchHost.configured(configuration())
    try:
        with TestClient(host.app) as client:
            assert client.get("/health").json()["authority"] == "identity_only"
            scope = Scope(tenant_id="host-tests", project_id="synthetic").model_dump()
            query = {"wire_version": "1", "scope": scope,
                "candidate": {"scope": scope, "candidate_id": "missing", "revision": 1},
                "sample": {"scope": scope, "sample_id": "missing", "revision": 1}}
            response = client.post("/v1/identities/resolve", json=query, headers={"Authorization": "Bearer " + "c"*32})
            assert response.status_code == 200 and response.json()["reason"] == "unknown_candidate"
    finally:
        host.close()


def test_migrator_credential_is_not_a_serving_role(research_database, monkeypatch):
    monkeypatch.setenv("RESEARCH_TEST_URL", research_database.set(username="research_migrator").render_as_string(hide_password=False))
    monkeypatch.setenv("RESEARCH_TEST_TOKEN", "c" * 32)
    with pytest.raises(ValueError, match="research_service_role_required"):
        ResearchHost.configured(configuration())


@pytest.mark.parametrize("mutation", [
    lambda x: x.update(unknown=True),
    lambda x: x.update(principals=[]),
    lambda x: x["principals"][0].update(actions=["publish"]),
    lambda x: x["principals"][0].update(actor_id=""),
    lambda x: x["principals"][0].update(token_env=""),
])
def test_invalid_host_configuration_fails_before_database(mutation):
    config = configuration()
    mutation(config)
    with pytest.raises(ValueError):
        ResearchHost.configured(config)
