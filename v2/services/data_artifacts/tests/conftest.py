"""Owner-local publication fixtures; real PostgreSQL is explicit opt-in."""

import hashlib
import json
import os
import uuid
from types import SimpleNamespace

import pytest
from amphora_contracts_artifacts import parse_command
from amphora_contracts_core import Scope
from amphora_data_artifacts.access import Credentials
from amphora_data_artifacts.api import create_app
from amphora_data_artifacts.persistence.migrate import upgrade
from amphora_data_artifacts.publication.model import ContentPolicy, Principal, UploadLimits
from amphora_data_artifacts.publication.uploads import Uploads
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
