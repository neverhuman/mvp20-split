import hashlib
import json
from dataclasses import replace

import pytest
from amphora_contracts_evidence import PreparedSource
from amphora_data_artifacts.access import Credentials
from amphora_data_artifacts.api import create_app
from fastapi.testclient import TestClient

pytestmark = pytest.mark.postgres


@pytest.fixture
def ingress(ingestion):
    e = ingestion
    credentials = Credentials([("c" * 32, e.principal),
        ("d" * 32, replace(e.principal, actions=frozenset({"read"}))),
        ("e" * 32, replace(e.principal, scope=e.principal.scope.model_copy(update={"project_id": "foreign"})))])
    with TestClient(create_app(e.env.uploads, e.env.storage, credentials, acquisition=e.workflow)) as client:
        yield e, client, {"Authorization": "Bearer " + "c" * 32}


@pytest.mark.parametrize("raw,format,disposition", [
    ("notes μ".encode(), "utf8_document", "normalized"),
    (b'{"value":"<0.5"}', "synthetic_lab_json", "quarantined"),
])
def test_public_stages_preserve_bytes_and_exact_replay(ingress, raw, format, disposition):
    e, client, headers = ingress
    source = e.source(raw, format).model_dump(mode="json")
    response = client.post("/v1/acquisition/prepare", json=source, headers=headers)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    prepared = PreparedSource.model_validate_json(response.content)
    content = prepared.content_json_utf8.encode("utf-8")
    assert hashlib.sha256(content).hexdigest() == prepared.sha256
    assert prepared.disposition == disposition
    assert client.post("/v1/acquisition/prepare", json=source, headers=headers).json() == response.json()
    output = e.publish(content, prepared.schema_ref)
    command = {"wire_version": "1", "source": source, "trace_id": "trace",
               "output": output.model_dump(mode="json")}
    retained = client.post("/v1/acquisition/retain", json=command, headers=headers)
    assert retained.status_code == 200, retained.text
    assert client.post("/v1/acquisition/retain", json=command, headers=headers).json() == retained.json()
    trace = client.get("/v1/acquisition/traces/trace", headers=headers)
    assert trace.status_code == 200 and trace.json()["disposition"] == disposition
    command["source"]["completeness"] = "partial"
    assert client.post("/v1/acquisition/retain", json=command, headers=headers).status_code == 409


def test_authentication_scope_and_history_are_separate(ingress):
    e, client, headers = ingress
    source = e.source().model_dump(mode="json")
    assert client.post("/v1/acquisition/prepare", json=source).status_code == 401
    assert client.post("/v1/acquisition/prepare", json=source,
                       headers={"Authorization": "Bearer " + "d" * 32}).status_code == 403
    assert client.post("/v1/acquisition/prepare", json=source,
                       headers={"Authorization": "Bearer " + "e" * 32}).status_code == 409
    assert client.get("/v1/acquisition/traces/absent", headers=headers).status_code == 404
    assert client.get("/v1/acquisition/traces/absent",
                      headers={"Authorization": "Bearer " + "d" * 32}).status_code == 403
    assert e.ledger.history(e.principal, "source", "r1") is None


@pytest.mark.parametrize("payload,media,status", [
    (b"{}", "text/plain", 415), (b"{}", "application/json", 422),
    (b'{"wire_version":"1","wire_version":"1"}', "application/json", 422),
    (b'{"x":NaN}', "application/json", 422), (b"[", "application/json", 422),
    (b"x" * 262145, "application/json", 413),
], ids=["media", "shape", "duplicate", "nonfinite", "syntax", "size"])
def test_ingress_rejects_unbounded_or_ambiguous_requests(ingress, payload, media, status):
    _, client, headers = ingress
    response = client.post("/v1/acquisition/prepare", content=payload, headers=headers | {"Content-Type": media})
    assert response.status_code == status
    assert len(response.content) < 128


def test_ingress_is_explicit_opt_in(ingestion):
    e = ingestion
    assert e.env.client.post("/v1/acquisition/prepare", content=json.dumps({})).status_code == 404
