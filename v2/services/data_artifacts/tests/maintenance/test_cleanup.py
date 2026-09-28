"""Provisional cleanup safety and capacity conservation using actual PostgreSQL."""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from amphora_contracts_artifacts import parse_command
from amphora_data_artifacts.maintenance.cleanup import Cleanup
from amphora_data_artifacts.publication.finalize import Finalizer
from amphora_data_artifacts.publication.model import UploadError
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.postgres


def age(env):
    # Explicit fixture-only clock setup through the isolated migration role.
    engine = create_engine(env.engine.url.set(username="artifact_migrator"))
    try:
        with engine.begin() as conn:
            conn.execute(text("UPDATE artifacts.uploads SET created_at=clock_timestamp()-interval '2 days' "
                "WHERE tenant_id=:tenant AND project_id=:project"), env.principal.bindings)
            conn.execute(text("UPDATE artifacts.upload_attempts SET expires_at=clock_timestamp()-interval '1 hour' "
                "WHERE tenant_id=:tenant AND project_id=:project"), env.principal.bindings)
    finally:
        engine.dispose()


def capacity(env):
    with env.engine.connect() as conn:
        return conn.execute(text("SELECT charged_bytes,active_streams FROM artifacts.capacity "
            "WHERE tenant_id=:tenant AND project_id=:project"), env.principal.bindings).one()


def cleaner(env):
    return Cleanup(env.uploads, env.storage), replace(env.principal, actions=frozenset({"cleanup"}))


def test_live_writer_defers_refund_and_retired_key_cannot_reopen(upload_env):
    e = upload_env
    upload = e.begin()
    attempt = e.uploads.start(e.principal, upload.upload_id)
    writer = e.storage.writer(attempt)
    writer.write(b"da")
    age(e)
    cleanup, principal = cleaner(e)
    try:
        assert cleanup.sweep(principal)["deferred"] == 1
        assert capacity(e) == (4, 1)
    finally:
        writer.close()
    assert cleanup.sweep(principal)["cleaned"] == 1
    assert capacity(e) == (0, 0)
    assert not e.storage.path(attempt.storage_key).exists()
    with pytest.raises(UploadError, match="storage_key_retired"):
        e.storage.writer(attempt)
    assert e.uploads.finish(e.principal, attempt, verified=False, actual_bytes=2) == "cleaned"
    assert cleanup.sweep(principal)["cleaned"] == 0
    assert capacity(e) == (0, 0)


def test_unopened_attempt_and_unused_begin_are_reclaimed_once(upload_env):
    e = upload_env
    first = e.begin()
    attempt = e.uploads.start(e.principal, first.upload_id)
    e.begin()
    age(e)
    cleanup, principal = cleaner(e)
    cleanup.sweep(principal)
    cleanup.sweep(principal)
    assert capacity(e) == (0, 0)
    with pytest.raises(UploadError, match="storage_key_retired"):
        e.storage.writer(attempt)


def test_failure_after_unlink_retries_without_double_refund(upload_env, monkeypatch):
    e = upload_env
    upload = e.begin()
    attempt = e.uploads.start(e.principal, upload.upload_id)
    writer = e.storage.writer(attempt)
    writer.write(b"data")
    writer.close()
    age(e)
    cleanup, principal = cleaner(e)
    original = e.storage.retire

    def interrupted(key):
        original(key)
        raise OSError("injected crash window")

    monkeypatch.setattr(e.storage, "retire", interrupted)
    assert cleanup.sweep(principal)["deferred"] == 1
    assert capacity(e) == (4, 0)
    monkeypatch.setattr(e.storage, "retire", original)
    cleanup.sweep(principal)
    assert capacity(e) == (0, 0)


def test_grace_and_grants_are_enforced(upload_env):
    e = upload_env
    e.begin()
    cleanup, principal = cleaner(e)
    with pytest.raises(UploadError, match="access_denied"):
        cleanup.sweep(e.principal)
    assert cleanup.sweep(principal)["cleaned"] == 0
    assert capacity(e) == (4, 0)


@pytest.mark.parametrize("mode", ["claimed", "retired", "writer"])
def test_killed_process_recovery(upload_env, mode):
    e = upload_env
    upload = e.begin()
    if mode != "writer":
        attempt = e.uploads.start(e.principal, upload.upload_id)
        writer = e.storage.writer(attempt)
        writer.write(b"data")
        writer.close()
        age(e)
    config = {"url": e.engine.url.render_as_string(hide_password=False), "scope": e.principal.scope.model_dump(),
              "limits": asdict(e.uploads.limits), "allowed": list(e.uploads.policy.allowed),
              "root": str(e.storage.root), "mode": mode, "upload": upload.upload_id}
    child = subprocess.Popen([sys.executable, "-I", str(Path(__file__).with_name("cleanup_probe.py"))],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        child.stdin.write(json.dumps(config) + "\n")
        child.stdin.flush()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(child.stdout.readline)
            try:
                assert future.result(timeout=15).strip() == mode
            except BaseException:
                child.kill()
                raise
        cleanup, principal = cleaner(e)
        if mode == "writer":
            age(e)
            assert cleanup.sweep(principal)["deferred"] == 1
        child.kill()
        child.communicate(timeout=10)
        assert capacity(e)[0] == 4
        assert cleanup.sweep(principal)["cleaned"] == 1
        assert capacity(e) == (0, 0)
        cleanup.sweep(principal)
        assert capacity(e) == (0, 0)
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=10)


def test_finalized_artifacts_survive_cleanup(upload_env):
    e = upload_env
    upload = e.begin()
    attempt = e.uploads.start(e.principal, upload.upload_id)
    writer = e.storage.writer(attempt)
    writer.write(b"data")
    writer.seal()
    writer.close()
    e.uploads.finish(e.principal, attempt, verified=True, actual_bytes=4)
    command = parse_command("artifacts.finalize", json.dumps({"identity": {
        "command_family": "artifacts.finalize", "command_id": "finalize", "actor_id": e.principal.actor_id,
        "scope": e.principal.scope.model_dump()}, "payload": {
        "upload_id": upload.upload_id, "content": upload.content.model_dump()}}))
    Finalizer(e.uploads, e.storage).finalize(e.principal, command)
    age(e)
    cleanup, principal = cleaner(e)
    assert cleanup.sweep(principal)["cleaned"] == 0
    assert e.storage.verify(attempt.storage_key, upload.content) == b"data"
    assert capacity(e) == (4, 0)
