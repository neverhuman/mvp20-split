"""Actual owner rights/database/storage plus authenticated ASGI content routes."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from amphora_data_artifacts.access import Credentials
from amphora_data_artifacts.api import create_app
from amphora_data_artifacts.publication.model import UploadError
from amphora_data_artifacts.source_rights.model import RightsError
from fastapi.testclient import TestClient

pytestmark = pytest.mark.postgres


def retained(e):
    source = e.source(b"synthetic source")
    prepared = e.workflow.prepare(e.principal, source)
    output = e.publish(prepared.content, prepared.output_schema)
    e.workflow.retain(e.principal, source, "trace", output)
    return source.reference.raw, output


def revision(e, *, uses=("read",), status="granted", expired=False):
    old = e.workflow.rights.history(e.principal, "fixture", 1)
    record = old.model_copy(update={"reference": old.reference.model_copy(update={"revision": 2}),
        "supersedes": old.reference, "allowed_uses": uses, "status": status,
        "expires_at": datetime.now(UTC) - timedelta(seconds=1) if expired else None})
    e.workflow.rights.publish(replace(e.principal, actions=frozenset({"manage_source_rights"})), record)


def test_processing_route_checks_current_use_while_ordinary_read_stays_readable(ingestion):
    e = ingestion
    references = retained(e)
    credentials = Credentials([("p" * 32, e.principal)])
    # Current rights must apply even when acquisition routes are disabled.
    with TestClient(create_app(e.env.uploads, e.env.storage, credentials)) as client:
        headers = {"Authorization": "Bearer " + "p" * 32}
        for ref in references:
            response = client.get(f"/v1/artifacts/{ref.artifact_id}/processing-content", headers=headers)
            assert response.status_code == 200
            assert response.content == e.reads.content(e.principal, ref.artifact_id)[1]
            assert response.headers["cache-control"] == "no-store"
            assert response.headers["x-content-type-options"] == "nosniff"
        revision(e)
        for ref in references:
            assert client.get(f"/v1/artifacts/{ref.artifact_id}/content", headers=headers).status_code == 200
            denied = client.get(f"/v1/artifacts/{ref.artifact_id}/processing-content", headers=headers)
            assert denied.status_code == 403 and "synthetic source" not in denied.text


@pytest.mark.parametrize("kind,code", [("expired", "rights_expired"), ("revoked", "rights_revoked")])
def test_processing_denies_expired_or_revoked_ancestry(ingestion, kind, code):
    e = ingestion
    references = retained(e)
    revision(e, uses=() if kind == "revoked" else ("read", "process"),
             status="revoked" if kind == "revoked" else "granted", expired=kind == "expired")
    for ref in references:
        with pytest.raises(RightsError, match=code):
            e.reads.processing_content(e.principal, ref.artifact_id)


@pytest.mark.parametrize("uses,code", [(("read",), "rights_use_denied"),
                                      (("read", "process"), "rights_epoch_changed")])
def test_process_rights_change_during_storage_read_is_fenced(ingestion, monkeypatch, uses, code):
    e = ingestion
    raw, _ = retained(e)
    verify = e.env.storage.verify
    def changed(key, descriptor):
        content = verify(key, descriptor)
        revision(e, uses=uses)
        return content
    monkeypatch.setattr(e.env.storage, "verify", changed)
    with pytest.raises(RightsError, match=code):
        e.reads.processing_content(e.principal, raw.artifact_id)


def test_processing_route_authentication_read_grant_scope_and_missing_identity(ingestion):
    e = ingestion
    raw, _ = retained(e)
    denied = replace(e.principal, actions=frozenset({"source_history"}))
    foreign = replace(e.principal, scope=e.principal.scope.model_copy(update={"project_id": "foreign"}))
    credentials = Credentials([("p" * 32, e.principal), ("q" * 32, denied), ("r" * 32, foreign)])
    with TestClient(create_app(e.env.uploads, e.env.storage, credentials)) as client:
        route = f"/v1/artifacts/{raw.artifact_id}/processing-content"
        assert client.get(route).status_code == 401
        assert client.get(route, headers={"Authorization": "Bearer " + "q" * 32}).status_code == 403
        assert client.get(route, headers={"Authorization": "Bearer " + "r" * 32}).status_code == 404
        assert client.get("/v1/artifacts/missing/processing-content",
                          headers={"Authorization": "Bearer " + "p" * 32}).status_code == 404


def test_processing_read_preserves_existing_byte_limit_before_storage_io(ingestion, monkeypatch):
    e = ingestion
    raw, _ = retained(e)
    e.reads.max_bytes = raw.size_bytes - 1
    def forbidden(*args):
        pytest.fail("Oversized processing read must not open storage")
    monkeypatch.setattr(e.env.storage, "verify", forbidden)
    with pytest.raises(UploadError, match="artifact_read_limit"):
        e.reads.processing_content(e.principal, raw.artifact_id)
