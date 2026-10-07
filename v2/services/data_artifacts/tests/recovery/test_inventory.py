"""Owner-local catalog audit, including real read-only PostgreSQL and immutable bytes."""

import json
from hashlib import sha256
from types import SimpleNamespace

import pytest
from amphora_contracts_artifacts import parse_command
from amphora_contracts_core import ArtifactRef, Scope
from amphora_data_artifacts.publication.finalize import Finalizer
from amphora_data_artifacts.recovery.inventory import (
    AuditTotals,
    CatalogAudit,
    CatalogEntry,
)
from amphora_data_artifacts.storage.local import LocalBytes
from sqlalchemy import create_engine


def test_streaming_integrity_failure_does_not_change_catalog_identity(tmp_path):
    key = 'a' * 32
    path = tmp_path / key
    path.write_bytes(b'data')
    ref = ArtifactRef(artifact_id='artifact', scope=Scope(tenant_id='fixture', project_id='recovery'),
        sha256=sha256(b'data').hexdigest(), size_bytes=4, media_type='application/octet-stream',
        schema_ref={'schema_id': 'fixture.bytes', 'version': '1', 'sha256': 'b' * 64})
    entry, storage = CatalogEntry(ref, key), LocalBytes(tmp_path)
    passed = AuditTotals()
    passed.observe(entry, entry.verify(storage, float('inf')))
    assert passed.result()['verified_bytes'] == 4
    with pytest.raises(TimeoutError, match='catalog_audit_deadline'):
        entry.verify(storage, 0)
    path.write_bytes(b'fake')
    failed = AuditTotals()
    failed.observe(entry, entry.verify(storage, float('inf')))
    assert failed.result()['failures'] == {'content_mismatch': 1}
    assert passed.result()['catalog_sha256'] == failed.result()['catalog_sha256']
    path.write_bytes(b'too long')
    assert entry.verify(storage, float('inf')) == 'content_mismatch'
    path.unlink()
    assert entry.verify(storage, float('inf')) == 'content_missing'
    path.mkdir()
    assert entry.verify(storage, float('inf')) == 'content_unreadable'


def test_bounds_reject_before_connection():
    audit = CatalogAudit(None, None)
    for args in ({'seconds': True}, {'seconds': 0}, {'maximum_entries': False}, {'maximum_entries': 1000001}):
        with pytest.raises(ValueError):
            audit.run(**args)


def publish(e):
    upload = e.begin()
    attempt = e.uploads.start(e.principal, upload.upload_id)
    writer = e.storage.writer(attempt)
    writer.write(b'data')
    writer.seal()
    writer.close()
    e.uploads.finish(e.principal, attempt, verified=True, actual_bytes=4)
    command = parse_command('artifacts.finalize', json.dumps({'identity': {
        'command_family': 'artifacts.finalize', 'command_id': 'recovery-' + upload.upload_id,
        'actor_id': e.principal.actor_id, 'scope': e.principal.scope.model_dump()},
        'payload': {'upload_id': upload.upload_id, 'content': upload.content.model_dump()}}))
    Finalizer(e.uploads, e.storage).finalize(e.principal, command)
    return attempt


@pytest.mark.postgres
def test_actual_catalog_integrity_missing_bytes_and_readonly_transaction(upload_env):
    e = upload_env
    attempt = publish(e)
    audit = CatalogAudit(e.engine, e.storage)
    lines = []
    result = audit.run(scope=e.principal.scope, inventory=SimpleNamespace(write=lines.append))
    assert (result['status'], result['checked'], result['verified']) == ('verified', 1, 1)
    assert result['pending_reservations'] == 0
    assert json.loads(lines[0])['storage_key'] == attempt.storage_key
    assert json.loads(lines[0])['integrity'] == 'verified'
    e.storage.path(attempt.storage_key).unlink()
    failed = audit.run(scope=e.principal.scope)
    assert failed['status'] == 'failed' and failed['failures'] == {'content_missing': 1}
    assert failed['catalog_sha256'] == result['catalog_sha256']
    # Audit never repairs or deletes the catalog reference.
    assert failed['checked'] == 1


@pytest.mark.postgres
def test_wrong_role_and_entry_bound_reject_without_false_success(upload_env):
    e = upload_env
    publish(e)
    e.begin()  # Provisional upload is deliberately not a finalized catalog item.
    assert CatalogAudit(e.engine, e.storage).run(scope=e.principal.scope)['checked'] == 1
    publish(e)
    with pytest.raises(TimeoutError, match='catalog_audit_incomplete'):
        CatalogAudit(e.engine, e.storage).run(scope=e.principal.scope, maximum_entries=1)
    foreign = create_engine(e.engine.url.set(username='artifact_migrator'))
    try:
        with pytest.raises(ValueError, match='catalog_audit_service_role'):
            CatalogAudit(foreign, e.storage).run(scope=e.principal.scope)
    finally:
        foreign.dispose()
