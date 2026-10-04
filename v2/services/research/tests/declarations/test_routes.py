import pytest
from amphora_research.transport.access import Credentials, Principal
from amphora_research.transport.api import create_app
from amphora_research.transport.host import ResearchHost
from amphora_research.transport.resolver import IdentityResolver
from fastapi.testclient import TestClient

TOKEN = "d" * 32
HEADERS = {"Authorization": "Bearer " + TOKEN}


def test_public_registration_readback_conflicts_and_separate_grants(registration):
    registrar, principal, question, need = registration
    credentials = Credentials([(TOKEN, Principal(principal.actor_id, principal.scope,
        principal.actions | {"read_declarations"})), ("r" * 32, Principal("reader", principal.scope,
        frozenset({"read_declarations"}))), ("q" * 32, Principal("question-only", principal.scope,
        frozenset({"declare_question"})))])
    with TestClient(create_app(IdentityResolver(registrar.ledger), credentials, registrar=registrar)) as client:
        qbody = question.model_dump(mode="json")
        assert client.post("/v1/questions", json=qbody).status_code == 401
        assert client.post("/v1/questions", json=qbody, headers={"Authorization": "Bearer " + "r"*32}).status_code == 403
        assert client.post("/v1/evidence-needs", json=need.model_dump(mode="json"), headers=HEADERS).status_code == 404
        response = client.post("/v1/questions", json=qbody, headers=HEADERS)
        assert response.status_code == 200 and response.json() == qbody
        assert response.headers["cache-control"] == "no-store"
        assert client.post("/v1/questions", json=qbody | {"objective": "changed"}, headers=HEADERS).status_code == 409
        assert client.post("/v1/questions/read", json=qbody["reference"], headers=HEADERS).json() == qbody
        nbody = need.model_dump(mode="json")
        assert client.post("/v1/evidence-needs", json=nbody, headers={"Authorization": "Bearer " + "q"*32}).status_code == 403
        assert client.post("/v1/evidence-needs", json=nbody | {"criterion_ids": ["unknown"]}, headers=HEADERS).status_code == 422
        assert client.post("/v1/evidence-needs", json=nbody, headers=HEADERS).json() == nbody
        foreign = qbody | {"applicability": qbody["applicability"] | {"scope": {"tenant_id": "else", "project_id": "else"}}}
        assert client.post("/v1/questions", json=foreign, headers=HEADERS).status_code == 403


@pytest.mark.parametrize("enabled", [False, True])
def test_configured_host_explicitly_enables_registration(registration, research_database, monkeypatch, enabled):
    _registrar, principal, question, _ = registration
    monkeypatch.setenv("DECLARATION_DB", research_database.render_as_string(hide_password=False))
    monkeypatch.setenv("DECLARATION_TOKEN", TOKEN)
    config = {"database_url_env": "DECLARATION_DB", "principals": [{"token_env": "DECLARATION_TOKEN",
        "actor_id": principal.actor_id, "scope": principal.scope.model_dump(),
        "actions": ["declare_question"] if enabled else ["read_declarations"]}], "declarations": enabled}
    host = ResearchHost.configured(config)
    try:
        with TestClient(host.app) as client:
            response = client.post("/v1/questions", json=question.model_dump(mode="json"), headers=HEADERS)
            assert response.status_code == (200 if enabled else 404)
    finally:
        host.close()


@pytest.mark.parametrize("flag", [None, False, "true", 1])
def test_grants_require_explicit_boolean_host_enablement(monkeypatch, flag):
    monkeypatch.setenv("DECLARATION_TOKEN", TOKEN)
    config = {"database_url_env": "NEVER_ACCESSED", "principals": [{"token_env": "DECLARATION_TOKEN",
        "actor_id": "a", "scope": {"tenant_id": "t", "project_id": "p"}, "actions": ["declare_question"]}]}
    if flag is not None:
        config["declarations"] = flag
    with pytest.raises(ValueError, match="declarations_configuration"):
        ResearchHost.configured(config)


@pytest.mark.parametrize("body,status", [(b'{"wire_version":1,"wire_version":2}', 422),
    (b'{"x":NaN}', 422), (b'{}', 422), (b'x' * 262145, 413)], ids=['duplicate', 'nonfinite', 'shape', 'oversize'])
def test_registration_keeps_strict_json_and_body_limit(registration, body, status):
    registrar, principal, _, _ = registration
    with TestClient(create_app(IdentityResolver(registrar.ledger), Credentials([(TOKEN, principal)]), registrar=registrar)) as client:
        response = client.post("/v1/questions", content=body, headers=HEADERS | {"Content-Type": "application/json"})
        assert response.status_code == status
