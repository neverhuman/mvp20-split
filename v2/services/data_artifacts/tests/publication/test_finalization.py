import hashlib
import json
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from threading import Barrier

import pytest
from amphora_contracts_artifacts import ContentDescriptor, parse_command
from amphora_data_artifacts.publication.finalize import Finalizer
from amphora_data_artifacts.publication.model import ContentPolicy, UploadError
from sqlalchemy import event, text

pytestmark = pytest.mark.postgres


def raw_final(e, receipt, key=None):
    return json.dumps({"identity": {"command_family": "artifacts.finalize", "command_id": key or uuid.uuid4().hex,
        "actor_id": "worker", "scope": e.principal.scope.model_dump()},
        "payload": {"upload_id": receipt.upload_id, "content": receipt.content.model_dump()}})


def ready(e, data=b"data"):
    receipt = e.begin(data)
    response = e.client.put(f"/v1/uploads/{receipt.upload_id}/content", content=data, headers=e.headers)
    assert response.status_code == 200
    return receipt


def count(e, table):
    with e.engine.connect() as conn:
        return conn.execute(text("SELECT count(*) FROM artifacts." + table +
            " WHERE tenant_id=:tenant AND project_id=:project"), e.principal.bindings).scalar_one()


def test_publish_replay_no_overwrite_or_double_charge(upload_env):
    e = upload_env
    receipt = ready(e)
    raw = raw_final(e, receipt)
    response = e.client.post("/v1/artifacts/finalize", content=raw, headers=e.headers)
    assert response.status_code == 200
    result = response.json()
    assert result["artifact"]["sha256"] == hashlib.sha256(b"data").hexdigest()
    assert e.client.post("/v1/artifacts/finalize", content=raw, headers=e.headers).json() == result
    assert e.client.post("/v1/artifacts/finalize", content=raw_final(e, receipt), headers=e.headers).json() == result
    assert count(e, "catalog") == 1 and count(e, "outbox") == 2
    assert e.client.put(f"/v1/uploads/{receipt.upload_id}/content", content=b"data", headers=e.headers).status_code == 409
    with e.engine.connect() as conn:
        assert conn.execute(text("SELECT charged_bytes FROM artifacts.capacity WHERE tenant_id=:tenant AND project_id=:project"),
                            e.principal.bindings).scalar_one() == 4


def test_changed_metadata_and_unready_upload(upload_env):
    e = upload_env
    receipt = e.begin()
    response = e.client.post("/v1/artifacts/finalize", content=raw_final(e, receipt), headers=e.headers)
    assert response.json()["reason_code"] == "upload_not_ready"
    bad = json.loads(raw_final(e, receipt))
    bad["payload"]["content"]["size_bytes"] = 3
    response = e.client.post("/v1/artifacts/finalize", json=bad, headers=e.headers)
    assert response.json()["reason_code"] == "content_descriptor_conflict"
    assert count(e, "catalog") == 0


def test_corruption_and_missing_bytes_never_publish(upload_env):
    e = upload_env
    receipt = ready(e)
    with e.engine.connect() as conn:
        key = conn.execute(text("SELECT storage_key FROM artifacts.upload_attempts WHERE tenant_id=:tenant AND project_id=:project"),
                           e.principal.bindings).scalar_one()
    path = e.storage.path(key)
    path.write_bytes(b"oops")  # Deliberate test-only corruption.
    response = e.client.post("/v1/artifacts/finalize", content=raw_final(e, receipt), headers=e.headers)
    assert response.status_code == 409 and response.json()["reason_code"] == "content_integrity_mismatch"
    path.unlink()
    response = e.client.post("/v1/artifacts/finalize", content=raw_final(e, receipt), headers=e.headers)
    assert response.status_code == 503 and count(e, "catalog") == 0


def test_generation_changed_during_verification(upload_env, monkeypatch):
    e = upload_env
    receipt = ready(e)
    original = e.storage.verify

    def verify(key, descriptor):
        data = original(key, descriptor)
        e.uploads.start(e.principal, receipt.upload_id)
        return data

    monkeypatch.setattr(e.storage, "verify", verify)
    response = e.client.post("/v1/artifacts/finalize", content=raw_final(e, receipt), headers=e.headers)
    assert response.json()["reason_code"] == "upload_selection_changed"
    assert count(e, "catalog") == 0


def test_atomic_rollback_after_catalog_before_receipt(upload_env):
    e = upload_env
    receipt = ready(e)
    raw = raw_final(e, receipt)

    def fault(_conn, _cursor, statement, _params, _context, _many):
        if statement.startswith("UPDATE artifacts.uploads SET status='finalized'"):
            raise RuntimeError("injected_after_catalog")

    event.listen(e.engine, "after_cursor_execute", fault)
    try:
        with pytest.raises(RuntimeError, match="injected_after_catalog"):
            Finalizer(e.uploads, e.storage).finalize(e.principal, parse_command("artifacts.finalize", raw))
    finally:
        event.remove(e.engine, "after_cursor_execute", fault)
    assert count(e, "catalog") == count(e, "outbox") == 0
    assert count(e, "audit_events") == 1
    assert e.client.post("/v1/artifacts/finalize", content=raw, headers=e.headers).status_code == 200


def test_concurrent_finalizations_share_catalog_identity(upload_env, monkeypatch):
    e = upload_env
    receipt = ready(e)
    barrier = Barrier(2, timeout=10)
    original = e.storage.verify

    def verify(key, descriptor):
        data = original(key, descriptor)
        barrier.wait()
        return data

    monkeypatch.setattr(e.storage, "verify", verify)

    def finalize(_):
        return Finalizer(e.uploads, e.storage).finalize(e.principal, parse_command("artifacts.finalize", raw_final(e, receipt)))

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(finalize, [0, 1]))
    assert results[0] == results[1] and count(e, "catalog") == 1


@pytest.mark.parametrize("media,payload,valid", [
    ("text/plain", b"hello", True), ("text/plain", b"\xff", False),
    ("application/json", b'{"value":3}', True), ("application/json", b"[]", False),
    ("application/json", b'{"a":1,"a":2}', False), ("application/json", b'{"a":NaN}', False),
    ("application/json", b'{"a":1e999}', False), ("application/json", b'{"a":"\\ud800"}', False),
])
def test_registered_content_validators(media, payload, valid):
    digest = hashlib.sha256(ContentPolicy.SCHEMAS[media]).hexdigest()
    policy = ContentPolicy(frozenset({(media, "fixture.content", "1", digest)}))
    descriptor = ContentDescriptor.model_validate_json(json.dumps({"sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload), "media_type": media,
        "schema_ref": {"schema_id": "fixture.content", "version": "1", "sha256": digest}}))
    if valid:
        policy.validate(descriptor, payload)
    else:
        with pytest.raises(UploadError, match="content_schema_mismatch"):
            policy.validate(descriptor, payload)


def test_schema_failure_is_terminal_and_never_catalogued(upload_env):
    e = upload_env
    media = "application/json"
    digest = hashlib.sha256(ContentPolicy.SCHEMAS[media]).hexdigest()
    e.uploads.policy = ContentPolicy(frozenset({(media, "fixture.json", "1", digest)}))
    raw = json.loads(e.raw(b"[]", media=media))
    raw["payload"]["content"]["schema_ref"].update(schema_id="fixture.json", sha256=digest)
    from amphora_contracts_artifacts import UploadReceipt
    receipt = UploadReceipt.model_validate_json(e.client.post("/v1/uploads", json=raw, headers=e.headers).text)
    assert e.client.put(f"/v1/uploads/{receipt.upload_id}/content", content=b"[]", headers=e.headers).status_code == 200
    command = raw_final(e, receipt)
    for _ in range(2):
        result = e.client.post("/v1/artifacts/finalize", content=command, headers=e.headers)
        assert result.json()["reason_code"] == "content_schema_mismatch"
    assert count(e, "catalog") == count(e, "outbox") == 0
    assert count(e, "audit_events") == 2  # Begin and one terminal rejection.


@pytest.mark.parametrize("barrier", ["verified", "committed"])
def test_killed_finalizer_resumes_same_command(upload_env, barrier):
    e = upload_env
    receipt = ready(e)
    command = raw_final(e, receipt)
    config = {"url": e.engine.url.render_as_string(hide_password=False),
              "scope": e.principal.scope.model_dump(), "limits": asdict(e.uploads.limits),
              "root": str(e.storage.root), "allowed": list(e.uploads.policy.allowed),
              "barrier": barrier, "command": command}
    worker = subprocess.Popen([sys.executable, "-I", str(Path(__file__).with_name("finalizer_probe.py"))],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        worker.stdin.write(json.dumps(config) + "\n")
        worker.stdin.flush()
        with ThreadPoolExecutor(1) as pool:
            try:
                reached = pool.submit(worker.stdout.readline).result(timeout=15).strip()
            except TimeoutError:
                worker.kill()
                raise
        assert reached == barrier
        worker.kill()
        worker.wait(timeout=10)
        assert count(e, "catalog") == (1 if barrier == "committed" else 0)
        result = e.client.post("/v1/artifacts/finalize", content=command, headers=e.headers)
        assert result.status_code == 200
        replay = e.client.post("/v1/artifacts/finalize", content=command, headers=e.headers)
        assert replay.json() == result.json()
        assert count(e, "catalog") == count(e, "outbox") == 1
    finally:
        if worker.poll() is None:
            worker.kill()
        worker.wait(timeout=10)
