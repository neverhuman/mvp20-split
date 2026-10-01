"""Public exact declaration reads preserve scope, revision and limited authority."""

import json

import pytest
from amphora_contracts_research import EvidenceNeed, ResearchQuestion
from amphora_research.transport.access import Credentials, Principal
from amphora_research.transport.api import create_app
from amphora_research.transport.resolver import IdentityResolver
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

HEADERS = {"Authorization": "Bearer " + "d" * 32}


@pytest.fixture
def declarations(ledger):
    store, scope = ledger
    schema = {"schema_id": "fixture", "version": "1", "sha256": "a" * 64}
    artifact = {"artifact_id": "context", "scope": scope.model_dump(), "sha256": "b" * 64,
                "media_type": "application/json", "schema_ref": schema, "size_bytes": 2}
    question = ResearchQuestion.model_validate_json(json.dumps({"wire_version": "1",
        "reference": {"scope": scope.model_dump(), "question_id": "q", "revision": 1},
        "objective": "Synthetic comparison", "applicability": artifact,
        "criteria": [{"criterion_id": "c", "description": "Method context"}], "supersedes": None}))
    need = EvidenceNeed.model_validate_json(json.dumps({"wire_version": "1",
        "reference": {"scope": scope.model_dump(), "need_id": "n", "revision": 1},
        "question": question.reference.model_dump(mode="json"), "criterion_ids": ["c"],
        "method": schema, "required_context": artifact, "supersedes": None}))
    store.publish(scope, question)
    store.publish(scope, need)
    credentials = Credentials([("d" * 32, Principal("reader", scope, frozenset({"read_declarations"}))),
        ("i" * 32, Principal("identity-reader", scope, frozenset({"resolve_identity"})))])
    with TestClient(create_app(IdentityResolver(store), credentials)) as client:
        yield client, store, question, need


@pytest.mark.parametrize("kind", ["questions", "evidence-needs"])
def test_exact_revision_read_and_old_history_are_only_declarations(declarations, kind):
    client, store, question, need = declarations
    record = question if kind == "questions" else need
    ref = record.reference
    later = record.model_copy(update={"reference": ref.model_copy(update={"revision": 2}), "supersedes": ref})
    store.publish(ref.scope, later)
    response = client.post(f"/v1/{kind}/read", json=ref.model_dump(mode="json"), headers=HEADERS)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == record.model_dump(mode="json")
    assert "accepted" not in response.json() and "scientific_authority" not in response.json()
    missing = ref.model_dump(mode="json") | {"revision": 3}
    assert client.post(f"/v1/{kind}/read", json=missing, headers=HEADERS).status_code == 404


@pytest.mark.parametrize("kind", ["questions", "evidence-needs"])
def test_foreign_scope_and_wrong_grant_denied_before_lookup(declarations, kind, monkeypatch):
    client, store, question, need = declarations
    body = (question if kind == "questions" else need).reference.model_dump(mode="json")

    def no_read(*_args):
        raise AssertionError("Unauthorized SQL lookup")

    monkeypatch.setattr(store, "read", no_read)
    route = f"/v1/{kind}/read"
    assert client.post(route, json=body).status_code == 401
    assert client.post(route, json=body, headers={"Authorization": "Bearer " + "i"*32}).status_code == 403
    body["scope"]["project_id"] = "foreign"
    assert client.post(route, json=body, headers=HEADERS).status_code == 403


def test_declaration_read_keeps_unavailable_distinct_from_missing(declarations, monkeypatch):
    client, store, question, _ = declarations

    def fail(*_args):
        raise SQLAlchemyError("secret diagnostic")

    monkeypatch.setattr(store, "read", fail)
    response = client.post("/v1/questions/read", json=question.reference.model_dump(mode="json"), headers=HEADERS)
    assert response.status_code == 503 and "secret" not in response.text


@pytest.mark.parametrize("body", [b'{"revision":1,"revision":2}', b'{"revision":NaN}', b'{}', b'\xff'])
def test_declaration_reads_use_bounded_strict_json(declarations, body):
    client, _, _, _ = declarations
    response = client.post("/v1/questions/read", content=body, headers=HEADERS | {"Content-Type": "application/json"})
    assert response.status_code == 422
