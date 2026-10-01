import json

import pytest
from amphora_contracts_research import CandidateRevision, IdentityResolution, SampleIdentity
from amphora_research.transport.access import Credentials, Principal
from amphora_research.transport.api import create_app
from amphora_research.transport.resolver import IdentityResolver
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError


@pytest.fixture
def api(ledger):
    store, scope = ledger
    ref = {"scope": scope.model_dump(), "candidate_id": "c", "revision": 1}
    artifact = {"artifact_id": "synthetic", "scope": scope.model_dump(), "sha256": "b" * 64,
        "media_type": "application/json", "size_bytes": 2,
        "schema_ref": {"schema_id": "fixture", "version": "1", "sha256": "a" * 64}}
    candidate = CandidateRevision.model_validate_json(json.dumps({"wire_version": "1", "reference": ref,
        "representation": artifact, "supersedes": None}))
    sample = SampleIdentity.model_validate_json(json.dumps({"wire_version": "1",
        "reference": {"scope": scope.model_dump(), "sample_id": "s", "revision": 1},
        "candidate": ref, "material_state": None, "identity_evidence": artifact, "supersedes": None}))
    store.publish(scope, candidate)
    store.publish(scope, sample)
    credentials = Credentials([("a" * 32, Principal("reader", scope, frozenset({"resolve_identity"}))),
                               ("b" * 32, Principal("denied", scope, frozenset()))])
    query = {"wire_version": "1", "scope": scope.model_dump(), "candidate": ref,
             "sample": sample.reference.model_dump(mode="json")}
    with TestClient(create_app(IdentityResolver(store), credentials)) as client:
        yield client, query, store


HEADERS = {"Authorization": "Bearer " + "a" * 32, "Content-Type": "application/json"}


def test_actual_owner_exact_identity_read_has_no_scientific_authority(api):
    client, query, _ = api
    response = client.post("/v1/identities/resolve", json=query, headers=HEADERS)
    assert response.status_code == 200
    result = IdentityResolution.model_validate_json(response.content)
    assert result.disposition == "matched" and result.reason == "exact_identity_only"
    assert result.authority == "identity_only"
    assert "artifact" not in response.text and "scientifically_accepted" not in response.text


def test_unknown_and_stale_revisions_remain_quarantined(api):
    client, query, _ = api
    query["sample"]["revision"] = 2
    response = client.post("/v1/identities/resolve", json=query, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["reason"] == "unknown_sample"
    query["candidate"]["revision"] = 2
    response = client.post("/v1/identities/resolve", json=query, headers=HEADERS)
    assert response.json()["reason"] == "unknown_candidate"
    assert response.json()["disposition"] == "quarantined"


@pytest.mark.parametrize("which", ["scope", "candidate", "sample"])
def test_each_foreign_scope_is_denied_before_lookup(api, which, monkeypatch):
    client, query, store = api
    target = query[which] if which == "scope" else query[which]["scope"]
    target["project_id"] = "foreign"

    def fail_read(*_args):
        raise AssertionError("unauthorized lookup")

    monkeypatch.setattr(store, "read", fail_read)
    assert client.post("/v1/identities/resolve", json=query, headers=HEADERS).status_code == 403


@pytest.mark.parametrize(("authorization", "status"), [(None, 401), ("Bearer unknown", 401), ("Bearer " + "b"*32, 403)])
def test_credentials_and_action_grants_are_required(api, authorization, status):
    client, query, _ = api
    headers = {"Content-Type": "application/json"}
    if authorization is not None:
        headers["Authorization"] = authorization
    response = client.post("/v1/identities/resolve", json=query, headers=headers)
    assert response.status_code == status
    assert response.json()["code"] in {"unauthorized", "access_denied"}


@pytest.mark.parametrize(("body", "status", "code"), [
    (b'{}', 422, "invalid_request"),
    (b'{"wire_version":"1","wire_version":"2"}', 422, "duplicate_json_key"),
    (b'{"wire_version":NaN}', 422, "invalid_json_constant"),
    (b'\xff', 422, "invalid_request"),
    (b' ' * 16385, 413, "request_limit"),
], ids=lambda value: f"bytes-{len(value)}" if isinstance(value, bytes) else str(value))
def test_malformed_requests_have_bounded_safe_errors(api, body, status, code):
    client, _, _ = api
    response = client.post("/v1/identities/resolve", content=body, headers=HEADERS)
    assert response.status_code == status and response.json() == {"code": code}


def test_database_failure_is_unavailable_not_unknown_identity(api, monkeypatch):
    client, query, store = api

    def fail_read(*_args):
        raise SQLAlchemyError("private diagnostic must not be returned")

    monkeypatch.setattr(store, "read", fail_read)
    response = client.post("/v1/identities/resolve", json=query, headers=HEADERS)
    assert response.status_code == 503 and response.json() == {"code": "identity_owner_unavailable"}


def test_content_type_is_explicit(api):
    client, query, _ = api
    headers = HEADERS | {"Content-Type": "text/plain"}
    assert client.post("/v1/identities/resolve", content=json.dumps(query), headers=headers).status_code == 415


@pytest.mark.parametrize("token", ["short", "a"*32 + "\n", "a"*512 + "b", "a"*31 + " ", "a"*31 + "μ"])
def test_bad_credential_configuration_fails_closed(token):
    with pytest.raises(ValueError, match="credential configuration"):
        Credentials([(token, None)])
