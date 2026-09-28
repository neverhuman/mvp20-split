"""Original publication results are scoped, immutable read projections."""

import json
from dataclasses import replace

import pytest
from amphora_contracts_artifacts import PublicationObservation, parse_command
from amphora_contracts_core import Scope
from amphora_data_artifacts.publication.inspection import PublicationHistory
from amphora_data_artifacts.publication.model import UploadError
from sqlalchemy import event, text

pytestmark = pytest.mark.postgres


def inspect(e, family, key, headers=None):
    return e.client.get(f"/v1/commands/{family}/{key}", headers=headers or e.headers)


def test_pending_then_original_upload_receipt(upload_env):
    e = upload_env
    command = parse_command("artifacts.begin_upload", e.raw(command_id="original"))
    registration = e.uploads.commands.register(command)
    pending = inspect(e, command.identity.command_family, "original")
    assert pending.status_code == 200
    observation = PublicationObservation.model_validate_json(pending.content)
    assert observation.identity == command.identity
    assert observation.request_sha256 == command.sha256
    assert observation.operation_id == registration.operation_id
    assert observation.outcome.status == "pending"
    receipt = e.uploads.begin(e.principal, command)
    accepted = inspect(e, command.identity.command_family, "original")
    assert accepted.json()["outcome"] == {"status": "uploaded", "receipt": receipt.model_dump(mode="json")}
    assert inspect(e, command.identity.command_family, "original").json() == accepted.json()


def test_finalized_and_rejected_original_outcomes(upload_env):
    e = upload_env
    upload = e.begin()
    payload = {"identity": {"command_family": "artifacts.finalize", "command_id": "unready",
        "actor_id": "worker", "scope": e.principal.scope.model_dump()},
        "payload": {"upload_id": upload.upload_id, "content": upload.content.model_dump()}}
    rejected = e.client.post("/v1/artifacts/finalize", json=payload, headers=e.headers)
    assert rejected.status_code == 409
    assert inspect(e, "artifacts.finalize", "unready").json()["outcome"] == {
        "status": "rejected", "reason_code": "upload_not_ready"}
    assert e.client.put(f"/v1/uploads/{upload.upload_id}/content", content=b"data", headers=e.headers).status_code == 200
    payload["identity"]["command_id"] = "published"
    final = e.client.post("/v1/artifacts/finalize", json=payload, headers=e.headers)
    assert final.status_code == 200
    result = inspect(e, "artifacts.finalize", "published")
    observation = PublicationObservation.model_validate_json(result.content)
    assert observation.outcome.status == "finalized"
    assert observation.outcome.receipt.model_dump(mode="json") == final.json()
    assert observation.request_sha256 == parse_command("artifacts.finalize", json.dumps(payload)).sha256
    # Subsequent publication does not change a rejected original command's history.
    assert inspect(e, "artifacts.finalize", "unready").json()["outcome"]["status"] == "rejected"


def test_no_cross_actor_scope_or_permission_lookup(upload_env):
    e = upload_env
    e.begin(command_id="private")
    other = {"Authorization": "Bearer " + "b" * 32}
    assert inspect(e, "artifacts.begin_upload", "private", other).status_code == 404
    assert inspect(e, "artifacts.finalize", "private", other).status_code == 403
    assert inspect(e, "artifacts.unknown", "private").status_code == 404
    assert e.client.get("/v1/commands/artifacts.begin_upload/private").status_code == 401
    foreign = replace(e.principal, scope=Scope(tenant_id="foreign", project_id="foreign"))
    with pytest.raises(UploadError, match="command_unavailable"):
        PublicationHistory(e.engine).read(foreign, "artifacts.begin_upload", "private")
    assert inspect(e, "artifacts.begin_upload", "missing").status_code == 404


def test_inspection_transaction_is_read_only_and_does_not_append(upload_env):
    e = upload_env
    e.begin(command_id="readonly")
    observed = []

    def probe(conn, _cursor, statement, _params, _context, _many):
        if statement.startswith("SELECT status,receipt,operation_id"):
            observed.append(conn.execute(text("SHOW transaction_read_only")).scalar_one())

    def counts():
        with e.engine.connect() as conn:
            return tuple(conn.execute(text(f"SELECT count(*) FROM artifacts.{table} "
                "WHERE tenant_id=:tenant AND project_id=:project"), e.principal.bindings).scalar_one()
                for table in ("commands", "uploads", "audit_events"))

    before = counts()
    event.listen(e.engine, "before_cursor_execute", probe)
    try:
        assert inspect(e, "artifacts.begin_upload", "readonly").status_code == 200
    finally:
        event.remove(e.engine, "before_cursor_execute", probe)
    assert observed == ["on"] and counts() == before
