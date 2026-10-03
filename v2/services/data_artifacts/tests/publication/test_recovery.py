"""Publication-owned expired stream probes, independent of representation workflows."""

from dataclasses import replace

import pytest
from amphora_data_artifacts.publication.model import UploadError
from amphora_data_artifacts.publication.recovery import StreamRecovery
from sqlalchemy import text

pytestmark = pytest.mark.postgres


def test_recovery_preserves_bytes_and_charge_and_fences_delayed_writer(upload_env):
    e = upload_env
    e.uploads.limits = replace(e.uploads.limits, seconds=1)
    upload = e.begin()
    attempt = e.uploads.start(e.principal, upload.upload_id)
    recovery = StreamRecovery(e.uploads, e.storage)
    writer = e.storage.writer(attempt)
    writer.write(b"dat")
    try:
        with e.engine.connect() as c:
            c.execute(text("SELECT pg_sleep(1.05)"))
        assert not recovery.settle_expired(e.principal, upload.upload_id)
    finally:
        writer.close()
    assert recovery.settle_expired(e.principal, upload.upload_id)
    assert e.storage.path(attempt.storage_key).read_bytes() == b"dat"
    assert not recovery.settle_expired(e.principal, upload.upload_id)
    with pytest.raises(UploadError, match="storage_key_retired"):
        e.storage.writer(attempt)
    with e.engine.connect() as c:
        row = c.execute(text("SELECT active_streams,charged_bytes FROM artifacts.capacity "
            "WHERE tenant_id=:tenant AND project_id=:project"), e.principal.bindings).one()
        assert tuple(row) == (0, 4)


def test_selected_bytes_are_not_exhausted_and_inspection_is_scoped(upload_env):
    e = upload_env
    e.uploads.limits = replace(e.uploads.limits, attempts=1)
    upload = e.begin()
    recovery = StreamRecovery(e.uploads, e.storage)
    with pytest.raises(UploadError, match="upload_unavailable"):
        recovery.inspect(replace(e.principal, actor_id="other"), upload.upload_id)
    with pytest.raises(UploadError, match="access_denied"):
        recovery.inspect(replace(e.principal, actions=frozenset()), upload.upload_id)
    attempt = e.uploads.start(e.principal, upload.upload_id)
    writer = e.storage.writer(attempt)
    try:
        writer.write(b"data")
        writer.seal()
    finally:
        writer.close()
    e.uploads.finish(e.principal, attempt, verified=True, actual_bytes=4)
    state = recovery.inspect(e.principal, upload.upload_id)
    assert state.selected["attempt_id"] == attempt.attempt_id
    assert state.terminal_reason(e.uploads.limits) is None
