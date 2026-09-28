import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from amphora_data_artifacts.publication.model import Principal, UploadError
from sqlalchemy import text

pytestmark = pytest.mark.postgres


def row(env, table):
    with env.engine.connect() as conn:
        return conn.execute(text("SELECT * FROM artifacts." + table +
            " WHERE tenant_id=:tenant AND project_id=:project"), env.principal.bindings).mappings().one()


def test_begin_replay_and_changed_identity(upload_env):
    e = upload_env
    command_id = uuid.uuid4().hex
    a = e.client.post("/v1/uploads", content=e.raw(command_id=command_id), headers=e.headers)
    b = e.client.post("/v1/uploads", content=e.raw(command_id=command_id), headers=e.headers)
    assert a.status_code == 200 and a.json() == b.json()
    assert row(e, "capacity")["charged_bytes"] == 4
    assert row(e, "capacity")["upload_count"] == 1
    changed = e.client.post("/v1/uploads", content=e.raw(b"different", command_id), headers=e.headers)
    assert changed.status_code == 409
    assert row(e, "audit_events")["payload"]["upload_id"] == a.json()["upload_id"]


@pytest.mark.parametrize("data,expected", [(b"da", "content_integrity_mismatch"),
    (b"data!", "content_size_mismatch"), (b"xxxx", "content_integrity_mismatch")])
def test_bad_stream_never_produces_artifact(upload_env, data, expected):
    e = upload_env
    receipt = e.begin()
    response = e.client.put(f"/v1/uploads/{receipt.upload_id}/content", content=data, headers=e.headers)
    assert response.status_code == 409 and response.json()["reason_code"] == expected
    assert row(e, "uploads")["selected_attempt"] is None
    assert row(e, "upload_attempts")["status"] == "failed"
    assert row(e, "capacity")["active_streams"] == 0
    with e.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM artifacts.catalog WHERE tenant_id=:tenant AND project_id=:project"),
                            e.principal.bindings).scalar_one() == 0


def test_success_is_provisional_and_retry_gets_new_attempt(upload_env):
    e = upload_env
    receipt = e.begin()
    route = f"/v1/uploads/{receipt.upload_id}/content"
    first = e.client.put(route, content=b"data", headers=e.headers)
    second = e.client.put(route, content=b"data", headers=e.headers)
    assert first.status_code == second.status_code == 200
    assert first.json()["status"] == "streamed" and "artifact" not in first.json()
    assert first.json()["attempt_id"] != second.json()["attempt_id"]
    assert second.json()["generation"] == 2
    assert row(e, "uploads")["selected_attempt"] == second.json()["attempt_id"]
    assert row(e, "capacity")["charged_bytes"] == 8  # Both immutable files retained.
    assert e.client.get("/health").json()["retention_available"] is False


def test_older_writer_finishing_last_cannot_replace_newer(upload_env):
    e = upload_env
    upload = e.begin()
    old = e.uploads.start(e.principal, upload.upload_id)
    new = e.uploads.start(e.principal, upload.upload_id)
    for attempt, expected in [(new, "streamed"), (old, "stale")]:
        writer = e.storage.writer(attempt)
        writer.write(b"data")
        writer.seal()
        writer.close()
        assert e.uploads.finish(e.principal, attempt, verified=True, actual_bytes=4) == expected
    assert row(e, "uploads")["selected_attempt"] == new.attempt_id
    assert e.storage.path(old.storage_key) != e.storage.path(new.storage_key)
    assert e.uploads.finish(e.principal, old, verified=False, actual_bytes=0) == "stale"
    assert row(e, "capacity")["charged_bytes"] == 8  # Duplicate settlement cannot refund twice.


def test_scope_actor_and_credentials_enforced(upload_env):
    e = upload_env
    assert e.client.post("/v1/uploads", content=e.raw()).status_code == 401
    assert e.client.post("/v1/uploads", content=e.raw(actor="other"), headers=e.headers).status_code == 403
    receipt = e.begin()
    assert e.client.put(f"/v1/uploads/{receipt.upload_id}/content", content=b"data",
                        headers={"Authorization": "Bearer " + "b" * 32}).status_code == 404
    other = Principal("worker", e.principal.scope.model_copy(update={"project_id": "another"}), frozenset({"upload"}))
    with pytest.raises(UploadError, match="upload_unavailable"):
        e.uploads.start(other, receipt.upload_id)
    assert row(e, "uploads")["generation"] == 0


def test_quota_race_and_stream_limit(upload_env):
    e = upload_env
    e.begin(b"a" * 64)
    barrier = Barrier(2)

    def begin(_):
        barrier.wait()
        try:
            return e.begin(b"b" * 64).upload_id
        except UploadError as error:
            return str(error)

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(begin, [0, 1]))
    assert results.count("capacity_exhausted") == 1
    assert row(e, "capacity")["charged_bytes"] == 128


def test_zero_bytes_attempts_and_concurrency_are_bounded(upload_env):
    e = upload_env
    receipt = e.begin(b"")
    first = e.uploads.start(e.principal, receipt.upload_id)
    second = e.uploads.start(e.principal, receipt.upload_id)
    with pytest.raises(UploadError, match="capacity_exhausted"):
        e.uploads.start(e.principal, receipt.upload_id)
    e.uploads.finish(e.principal, first, verified=False, actual_bytes=0)
    e.uploads.finish(e.principal, second, verified=False, actual_bytes=0)
    third = e.uploads.start(e.principal, receipt.upload_id)
    e.uploads.finish(e.principal, third, verified=False, actual_bytes=0)
    with pytest.raises(UploadError, match="attempt_limit"):
        e.uploads.start(e.principal, receipt.upload_id)


def test_descriptor_rejection_replays_and_unknown_format_denied(upload_env):
    e = upload_env
    key = uuid.uuid4().hex
    for _ in range(2):
        response = e.client.post("/v1/uploads", content=e.raw(b"a" * 65, key), headers=e.headers)
        assert response.status_code == 413
    assert row(e, "capacity")["charged_bytes"] == 0
    assert row(e, "commands")["status"] == "rejected"
    assert e.client.post("/v1/uploads", content=e.raw(media="text/html"), headers=e.headers).status_code == 409
