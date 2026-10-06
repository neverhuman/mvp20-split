from dataclasses import replace

import pytest
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.reader import AssessmentPeerUnavailable
from amphora_research.transport.access import Credentials
from amphora_research.transport.api import create_app
from amphora_research.transport.host import ResearchHost
from amphora_research.transport.resolver import IdentityResolver
from fastapi.testclient import TestClient

TOKEN = "c" * 32
HEADERS = {"Authorization": "Bearer " + TOKEN}


def client_for(registrar, principal):
    credentials = Credentials(
        [
            (TOKEN, principal),
            ("r" * 32, replace(principal, actions=frozenset({"read_candidate"}))),
        ]
    )
    return TestClient(
        create_app(
            IdentityResolver(registrar.ledger), credentials, candidates=registrar
        )
    )


def test_candidate_routes_separate_grants_and_retained_read(candidate_registration):
    registrar, principal, record, peer = candidate_registration
    body = record.model_dump(mode="json")
    with client_for(registrar, principal) as client:
        assert client.post("/v1/candidates", json=body).status_code == 401
        assert (
            client.post(
                "/v1/candidates",
                json=body,
                headers={"Authorization": "Bearer " + "r" * 32},
            ).status_code
            == 403
        )
        missing = client.post(
            "/v1/candidates/read", json=body["reference"], headers=HEADERS
        )
        assert missing.status_code == 404
        response = client.post("/v1/candidates", json=body, headers=HEADERS)
        assert response.status_code == 200 and response.json() == body
        assert response.headers["cache-control"] == "no-store"
        peer.error = AssessmentError("peer_access_denied")
        assert (
            client.post("/v1/candidates", json=body, headers=HEADERS).status_code == 403
        )
        assert (
            client.post(
                "/v1/candidates/read", json=body["reference"], headers=HEADERS
            ).json()
            == body
        )
        peer.error = AssessmentError("reference_unavailable")
        assert (
            client.post("/v1/candidates", json=body, headers=HEADERS).status_code == 404
        )
        peer.error = AssessmentPeerUnavailable("peer_unavailable")
        assert (
            client.post("/v1/candidates", json=body, headers=HEADERS).status_code == 503
        )


@pytest.mark.parametrize(
    "raw,status",
    [(b"{}", 422), (b'{"x":NaN}', 422), (b'{"x":1,"x":2}', 422), (b"x" * 262145, 413)],
    ids=["shape", "nonfinite", "duplicate", "capacity"],
)
def test_candidate_body_is_bounded_strict_json(candidate_registration, raw, status):
    registrar, principal, _, peer = candidate_registration
    with client_for(registrar, principal) as client:
        response = client.post(
            "/v1/candidates",
            content=raw,
            headers=HEADERS | {"Content-Type": "application/json"},
        )
        assert response.status_code == status and peer.calls == 0


def test_write_is_absent_without_explicit_configuration(candidate_registration):
    registrar, principal, record, _ = candidate_registration
    with TestClient(
        create_app(
            IdentityResolver(registrar.ledger), Credentials([(TOKEN, principal)])
        )
    ) as client:
        assert (
            client.post(
                "/v1/candidates", json=record.model_dump(mode="json"), headers=HEADERS
            ).status_code
            == 404
        )


def test_write_grant_requires_configuration_before_database(monkeypatch):
    monkeypatch.setenv("CANDIDATE_TOKEN", TOKEN)
    config = {
        "database_url_env": "NEVER_READ",
        "principals": [
            {
                "token_env": "CANDIDATE_TOKEN",
                "actor_id": "actor",
                "scope": {"tenant_id": "t", "project_id": "p"},
                "actions": ["declare_candidate"],
            }
        ],
    }
    with pytest.raises(ValueError, match="candidate_configuration_required"):
        ResearchHost.configured(config)


@pytest.mark.parametrize("enabled", [False, True])
def test_configured_candidate_host(
    candidate_registration, research_database, monkeypatch, enabled
):
    registrar, principal, _record, _ = candidate_registration
    monkeypatch.setenv(
        "CANDIDATE_DB", research_database.render_as_string(hide_password=False)
    )
    monkeypatch.setenv("CANDIDATE_TOKEN", TOKEN)
    monkeypatch.setenv("CANDIDATE_DATA_TOKEN", "a" * 32)
    config = {
        "database_url_env": "CANDIDATE_DB",
        "principals": [
            {
                "token_env": "CANDIDATE_TOKEN",
                "actor_id": principal.actor_id,
                "scope": principal.scope.model_dump(),
                "actions": ["declare_candidate", "read_candidate"]
                if enabled
                else ["read_candidate"],
            }
        ],
    }
    if enabled:
        profile = registrar.profiles.profiles[0]
        config["candidates"] = {
            "data": {
                "endpoint": "http://127.0.0.1:1",
                "token_env": "CANDIDATE_DATA_TOKEN",
            },
            "profiles": [
                {
                    "schema": profile.schema.model_dump(),
                    "kind": profile.kind,
                    "semantic_profile": profile.semantic_profile.model_dump(),
                }
            ],
        }
    host = ResearchHost.configured(config)
    try:
        paths = {route.path for route in host.app.routes}
        assert ("/v1/candidates" in paths) is enabled
        assert "/v1/candidates/read" in paths
        assert host.app.state.candidates_enabled is enabled
    finally:
        host.close()
