import json

import pytest
from amphora_contracts_research import EvidenceAssessmentStatus
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.reader import AssessmentPeerUnavailable
from amphora_research.transport.access import Credentials, Principal
from amphora_research.transport.api import create_app
from amphora_research.transport.assessments import AssessmentOperations
from amphora_research.transport.host import ResearchHost
from amphora_research.transport.resolver import IdentityResolver
from fastapi.testclient import TestClient

pytestmark = pytest.mark.postgres
HEADERS = {"Authorization": "Bearer " + "a" * 32, "Content-Type": "application/json"}


@pytest.fixture
def assessment_api(assessment_store, monkeypatch):
    store, bound, resolved = assessment_store
    operations = AssessmentOperations(store.engine, [bound.configured.document.model_dump(mode="json")],
                                      "http://127.0.0.1:1", "b" * 32, "publisher", "issuer", "p" * 32)
    actions = frozenset({"assess", "read_assessment", "publish_assessment", "read_assessment_publication"})
    credentials = Credentials([
        ("a" * 32, Principal(bound.actor_id, bound.request.profile.scope, actions)),
        ("i" * 32, Principal(bound.actor_id, bound.request.profile.scope, frozenset({"resolve_identity"}))),
        ("x" * 32, Principal("another", bound.request.profile.scope, actions)),
        ("s" * 32, Principal(bound.actor_id, bound.request.profile.scope.model_copy(update={"project_id": "other"}), actions)),
    ])
    from amphora_research.persistence.ledger import IdentityLedger

    monkeypatch.setattr("amphora_research.transport.assessments.AssessmentResolver.resolve", lambda self, selected: resolved)
    with TestClient(create_app(IdentityResolver(IdentityLedger(store.engine)), credentials, operations)) as client:
        yield client, bound.request.model_dump(mode="json"), operations, store


def test_authenticated_assessment_replay_and_read_do_not_reevaluate(assessment_api, monkeypatch):
    client, request, operations, _ = assessment_api
    assert client.post("/v1/assessments/read", json=request, headers=HEADERS).status_code == 404
    first = client.post("/v1/assessments", json=request, headers=HEADERS)
    assert first.status_code == 200
    result = EvidenceAssessmentStatus.model_validate_json(first.content)
    assert result.outcome.status == "assessed" and not result.outcome.assessment.scientifically_established
    operations.profiles.clear()

    def forbidden(*args):
        raise AssertionError("replay must not resolve")

    monkeypatch.setattr("amphora_research.transport.assessments.AssessmentResolver.resolve", forbidden)
    for path in ("/v1/assessments", "/v1/assessments/read"):
        response = client.post(path, json=request, headers=HEADERS)
        assert response.content == first.content and response.headers["cache-control"] == "no-store"
    changed = request | {"receipts": [result.outcome.assessment.subject.model_dump(mode="json")]}
    assert client.post("/v1/assessments", json=changed, headers=HEADERS).status_code == 409
    assert client.post("/v1/assessments/read", json=changed, headers=HEADERS).status_code == 409


@pytest.mark.parametrize("token,status", [(None, 401), ("i", 403), ("s", 403), ("x", 403)])
def test_identity_grants_wrong_scope_and_other_actor_cannot_access_assessment(assessment_api, token, status):
    client, request, _, _ = assessment_api
    assert client.post("/v1/assessments", json=request, headers=HEADERS).status_code == 200
    headers = {} if token is None else {"Authorization": "Bearer " + token * 32}
    for path in ("/v1/assessments", "/v1/assessments/read"):
        assert client.post(path, json=request, headers=headers).status_code == status
    selection = {"wire_version": "1", "scope": request["profile"]["scope"], "assessment_id": request["assessment_id"]}
    for path in ("/v1/assessment-publications", "/v1/assessment-publications/read"):
        assert client.post(path, json=selection, headers=headers).status_code == status


@pytest.mark.parametrize("error,status", [(AssessmentPeerUnavailable("offline"), 503),
                                         (AssessmentError("peer_access_denied"), 403),
                                         (AssessmentError("invalid_evidence_payload"), 422)])
def test_resolution_failure_never_becomes_sufficient_result(assessment_api, monkeypatch, error, status):
    client, request, _, _ = assessment_api

    def fail(*args):
        raise error

    monkeypatch.setattr("amphora_research.transport.assessments.AssessmentResolver.resolve", fail)
    assert client.post("/v1/assessments", json=request, headers=HEADERS).status_code == status
    read = client.post("/v1/assessments/read", json=request, headers=HEADERS)
    assert read.status_code == 200 and read.json()["outcome"]["status"] == "pending"


def test_unknown_profile_publication_without_result_and_unavailable_peer(assessment_api):
    client, request, _, _ = assessment_api
    selection = {"wire_version": "1", "scope": request["profile"]["scope"], "assessment_id": request["assessment_id"]}
    assert client.post("/v1/assessment-publications/read", json=selection, headers=HEADERS).status_code == 404
    assert client.post("/v1/assessment-publications", json=selection, headers=HEADERS).status_code == 404
    bad = request | {"profile": request["profile"] | {"sha256": "0" * 64}}
    assert client.post("/v1/assessments", json=bad, headers=HEADERS).status_code == 404
    assert client.post("/v1/assessments", json=request, headers=HEADERS).status_code == 200
    assert client.post("/v1/assessment-publications", json=selection, headers=HEADERS).status_code == 503
    assert client.post("/v1/assessment-publications/read", json=selection, headers=HEADERS).json()["outcome"] == {"status": "pending"}


@pytest.mark.parametrize("body,status", [(b"{" + b"x" * 262144, 413),
                                       (b'{"wire_version":"1","wire_version":"1"}', 422),
                                       (b'{"wire_version":NaN}', 422)], ids=["oversized", "duplicate", "nonfinite"])
def test_assessment_body_bounds_and_strict_json(assessment_api, body, status):
    client, _, _, _ = assessment_api
    assert client.post("/v1/assessments", content=body, headers=HEADERS).status_code == status


def test_optional_host_configuration_and_profile_boundaries(assessment_store, monkeypatch):
    store, bound, _ = assessment_store
    monkeypatch.setenv("RESEARCH_TEST_DB", store.engine.url.render_as_string(hide_password=False))
    monkeypatch.setenv("RESEARCH_TEST_TOKEN", "a" * 32)
    config = {"database_url_env": "RESEARCH_TEST_DB", "principals": [{"token_env": "RESEARCH_TEST_TOKEN",
        "actor_id": bound.actor_id, "scope": bound.request.profile.scope.model_dump(mode="json"), "actions": ["assess"]}],
        "assessment": {"profiles": [bound.configured.document.model_dump(mode="json")],
                       "data": {"endpoint": "http://127.0.0.1:1", "token_env": "RESEARCH_TEST_TOKEN"},
                       "publication": {"actor_id": "publisher", "issuer_id": "issuer", "token_env": "RESEARCH_TEST_TOKEN"}}}
    host = ResearchHost.configured(config)
    try:
        with TestClient(host.app) as client:
            assert client.get("/health").json()["authority"] == "synthetic_assessment"
    finally:
        host.close()
    absent = dict(config)
    del absent["assessment"]
    with pytest.raises(ValueError, match="configuration_required"):
        ResearchHost.configured(absent)
    for profiles in ([], config["assessment"]["profiles"] * 2):
        changed = json.loads(json.dumps(config))
        changed["assessment"]["profiles"] = profiles
        with pytest.raises(ValueError, match="profile"):
            ResearchHost.configured(changed)
