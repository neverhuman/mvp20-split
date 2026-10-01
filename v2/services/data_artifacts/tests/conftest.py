"""Owner-local publication/acquisition fixtures; PostgreSQL is explicit opt-in."""

import hashlib
import json
import os
import uuid
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_contracts_artifacts import parse_command
from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_evidence import SourceRevision, SourceRightsRevision, prepared_schema
from amphora_data_artifacts.access import Credentials
from amphora_data_artifacts.acquisition.ledger import AcquisitionLedger
from amphora_data_artifacts.acquisition.profiles import PreparedContentRule
from amphora_data_artifacts.acquisition.workflow import AcquisitionWorkflow
from amphora_data_artifacts.api import create_app
from amphora_data_artifacts.persistence.migrate import upgrade
from amphora_data_artifacts.publication.model import ContentPolicy, Principal, UploadLimits
from amphora_data_artifacts.publication.uploads import Uploads
from amphora_data_artifacts.reads import ArtifactReads
from amphora_data_artifacts.source_rights.ledger import SourceRights
from amphora_data_artifacts.storage.local import LocalBytes
from fastapi.testclient import TestClient
from postgres_fixture import owned_state
from sqlalchemy import URL, create_engine


@pytest.fixture(scope="session")
def artifact_database():
    if os.environ.get("AMPHORA_TEST_POSTGRES") != "1":
        pytest.skip("Explicit PostgreSQL opt-in required")
    state = owned_state()
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="artifact_migrator", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    upgrade(url.render_as_string(hide_password=False))
    return url.set(username="artifact_service")


@pytest.fixture
def upload_env(artifact_database, tmp_path):
    engine = create_engine(artifact_database, connect_args={"options": "-c statement_timeout=5000"})
    scope = Scope(tenant_id="upload-tests", project_id=uuid.uuid4().hex)
    principal = Principal("worker", scope, frozenset({"upload", "finalize"}))
    schema_hash = hashlib.sha256(b'{"type":"string","contentEncoding":"base64"}').hexdigest()
    policy = ContentPolicy(frozenset({("application/octet-stream", "fixture.bytes", "1", schema_hash)}))
    limits = UploadLimits(max_bytes=64, scope_bytes=128, streams=2, uploads=4, attempts=3, seconds=10)
    uploads = Uploads(engine, limits, policy)
    storage = LocalBytes(tmp_path)
    credentials = Credentials([("a" * 32, principal),
                               ("b" * 32, Principal("other", scope, frozenset({"upload"})))])

    def raw(data=b"data", command_id=None, actor="worker", media="application/octet-stream"):
        return json.dumps({"identity": {"command_family": "artifacts.begin_upload",
            "command_id": command_id or uuid.uuid4().hex, "actor_id": actor, "scope": scope.model_dump()},
            "payload": {"content": {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
                "media_type": media, "schema_ref": {"schema_id": "fixture.bytes", "version": "1", "sha256": schema_hash}}}})

    def begin(data=b"data", command_id=None):
        return uploads.begin(principal, parse_command("artifacts.begin_upload", raw(data, command_id)))

    with TestClient(create_app(uploads, storage, credentials)) as client:
        yield SimpleNamespace(engine=engine, principal=principal, uploads=uploads, storage=storage,
                              raw=raw, begin=begin, client=client, headers={"Authorization": "Bearer " + "a" * 32})
    engine.dispose()


@pytest.fixture
def grant_source_rights(upload_env):
    principal = replace(upload_env.principal, actions=frozenset({"manage_source_rights"}))

    def grant(reference):
        record = SourceRightsRevision(wire_version="1", reference=reference, supersedes=None, status="granted",
                                      allowed_uses=("read", "process"), expires_at=None, retention="retain_audit_payload")
        return SourceRights(upload_env.engine).publish(principal, record)

    return grant


@pytest.fixture
def ingestion(upload_env, grant_source_rights):
    e = upload_env
    profiles = [prepared_schema(kind) for kind in ("document", "lab")]
    e.uploads.policy = ContentPolicy(e.uploads.policy.allowed | frozenset(
        ("application/json", ref.schema_id, ref.version, ref.sha256) for ref in profiles),
        rules=(PreparedContentRule("document"), PreparedContentRule("lab")))
    e.uploads.limits = UploadLimits(max_bytes=65536, scope_bytes=1048576)
    principal = replace(e.principal, actions=frozenset({"read", "acquire", "source_history"}))
    ledger = AcquisitionLedger(e.engine)
    reads = ArtifactReads(e.engine, e.storage, 65536)

    def publish(content, schema=None):
        envelope = json.loads(e.raw(content))
        if schema is not None:
            envelope["payload"]["content"].update(media_type="application/json",
                                                 schema_ref=schema.model_dump(mode="json"))
        receipt = e.uploads.begin(e.principal, parse_command("artifacts.begin_upload", json.dumps(envelope)))
        response = e.client.put(f"/v1/uploads/{receipt.upload_id}/content", content=content, headers=e.headers)
        assert response.status_code == 200
        response = e.client.post("/v1/artifacts/finalize", headers=e.headers, json={
            "identity": {"command_family": "artifacts.finalize", "command_id": uuid.uuid4().hex,
                         "actor_id": "worker", "scope": principal.scope.model_dump()},
            "payload": {"upload_id": receipt.upload_id, "content": receipt.content.model_dump(mode="json")}})
        assert response.status_code == 200, response.text
        return ArtifactRef.model_validate_json(json.dumps(response.json()["artifact"]))

    def source(content=b"research notes", format="utf8_document"):
        revision = SourceRevision.model_validate_json(json.dumps({"wire_version": "1",
            "reference": {"scope": principal.scope.model_dump(), "source_id": "source", "revision_id": "r1",
                          "raw": publish(content).model_dump(mode="json")},
            "delivery": {"issuer_id": "fixture", "delivery_id": "d1"},
            "method": {"connector_id": "fixture", "connector_version": "1",
                       "configuration_sha256": hashlib.sha256(b"{}").hexdigest(), "format": format},
            "rights": {"scope": principal.scope.model_dump(), "rights_id": "fixture", "revision": 1},
            "supersedes": None, "completeness": "complete"}))
        grant_source_rights(revision.rights)
        return revision

    return SimpleNamespace(workflow=AcquisitionWorkflow(reads, ledger), ledger=ledger, reads=reads,
                           principal=principal, publish=publish, source=source, env=e)
