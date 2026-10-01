import hashlib
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_evidence import ConversionTrace, SourceRevision
from amphora_data_artifacts.acquisition.ledger import AcquisitionLedger
from amphora_data_artifacts.acquisition.provenance import ProvenanceError, SourceDocument
from amphora_data_artifacts.publication.model import UploadError
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres
DATA = b"mass=12"


@pytest.fixture
def acquisition(upload_env, grant_source_rights):
    e = upload_env
    receipt = e.begin(DATA)
    response = e.client.put(f"/v1/uploads/{receipt.upload_id}/content", content=DATA, headers=e.headers)
    assert response.status_code == 200
    raw = {"identity": {"command_family": "artifacts.finalize", "command_id": uuid.uuid4().hex,
        "actor_id": "worker", "scope": e.principal.scope.model_dump()},
        "payload": {"upload_id": receipt.upload_id, "content": receipt.content.model_dump()}}
    response = e.client.post("/v1/artifacts/finalize", json=raw, headers=e.headers)
    assert response.status_code == 200
    artifact = ArtifactRef.model_validate_json(json.dumps(response.json()["artifact"]))
    principal = replace(e.principal, actions=frozenset({"acquire", "source_history"}))
    revision = SourceRevision.model_validate_json(json.dumps({"wire_version": "1",
        "reference": {"scope": principal.scope.model_dump(), "source_id": "source", "revision_id": "r1",
                      "raw": artifact.model_dump(mode="json")},
        "delivery": {"issuer_id": "fixture", "delivery_id": "d1"},
        "method": {"connector_id": "fixture", "connector_version": "1",
                   "configuration_sha256": "a" * 64, "format": "utf8_document"},
        "rights": {"scope": principal.scope.model_dump(), "rights_id": "unresolved-fixture", "revision": 1},
        "supersedes": None, "completeness": "complete"}))
    grant_source_rights(revision.rights)
    return AcquisitionLedger(e.engine), principal, revision, e


def trace(revision):
    ref = revision.reference
    span = {"source": ref.model_dump(mode="json"), "unit": "byte", "start": 0, "end": len(DATA),
            "sha256": hashlib.sha256(DATA).hexdigest()}
    return ConversionTrace.model_validate_json(json.dumps({"wire_version": "1", "scope": ref.scope.model_dump(),
        "trace_id": "t1", "source": ref.model_dump(mode="json"),
        "source_schema": ref.raw.schema_ref.model_dump(mode="json"),
        "target_schema": ref.raw.schema_ref.model_dump(mode="json"),
        "converter_id": "identity", "converter_version": "1", "configuration_sha256": "a" * 64,
        "transforms": [{"transform_id": "copy", "version": "1", "configuration_sha256": "a" * 64,
                        "kind": "deterministic"}], "output": ref.raw.model_dump(mode="json"),
        "fields": [{"target_path": "/raw", "origin": "copied", "spans": [span], "step_indices": [0]}],
        "warnings": [], "disposition": "normalized"}))


def correction(first, revision_id="r2", delivery_id="d2"):
    return first.model_copy(update={"reference": first.reference.model_copy(update={"revision_id": revision_id}),
        "delivery": first.delivery.model_copy(update={"delivery_id": delivery_id}), "supersedes": first.reference})


def test_delivery_replay_corrections_and_historical_replacement(acquisition):
    store, principal, first, _ = acquisition
    source = SourceDocument(first.reference, DATA)
    assert store.register(principal, first, source) == first
    second = correction(first)
    store.register(principal, second, SourceDocument(second.reference, DATA))
    replacement = AcquisitionLedger(store.engine)
    assert replacement.register(principal, first, source) == first
    assert replacement.history(principal, "source", "r1") == first
    assert replacement.history(principal, "source", "r2") == second
    with pytest.raises(ProvenanceError, match="delivery_conflict"):
        store.register(principal, first.model_copy(update={"completeness": "partial"}), source)
    stale = correction(first, "r3", "d3")
    with pytest.raises(ProvenanceError, match="source_head_conflict"):
        store.register(principal, stale, SourceDocument(stale.reference, DATA))


def test_same_delivery_contends_across_source_ids(acquisition):
    store, principal, first, _ = acquisition
    barrier = Barrier(2)

    def write(source_id):
        record = first.model_copy(update={"reference": first.reference.model_copy(update={"source_id": source_id})})
        barrier.wait(timeout=5)
        try:
            store.register(principal, record, SourceDocument(record.reference, DATA))
            return "published"
        except ProvenanceError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(write, ["left", "right"])) == ["delivery_conflict", "published"]


def test_trace_identity_is_immutable_and_requires_registered_source(acquisition):
    store, principal, first, _ = acquisition
    source = SourceDocument(first.reference, DATA)
    record = trace(first)
    with pytest.raises(ProvenanceError, match="unknown_source_revision"):
        store.retain_trace(principal, record, source, DATA)
    store.register(principal, first, source)
    reference = store.retain_trace(principal, record, source, DATA)
    assert store.retain_trace(principal, record, source, DATA) == reference
    assert store.trace_history(principal, "t1") == record
    changed = record.model_copy(update={"converter_version": "2"})
    with pytest.raises(ProvenanceError, match="trace_identity_conflict"):
        store.retain_trace(principal, changed, source, DATA)
    changed = changed.model_copy(update={"trace_id": "t2"})
    assert store.retain_trace(principal, changed, source, DATA).trace_id == "t2"


def test_missing_or_forged_catalog_reference_never_registers(acquisition):
    store, principal, first, _ = acquisition
    for patch, code in (({"artifact_id": "not-finalized"}, "artifact_not_finalized"),
                        ({"media_type": "text/other"}, "catalog_reference_mismatch")):
        record = first.model_copy(update={"reference": first.reference.model_copy(
            update={"raw": first.reference.raw.model_copy(update=patch)})})
        with pytest.raises(ProvenanceError, match=code):
            store.register(principal, record, SourceDocument(record.reference, DATA))
    assert store.history(principal, "source", "r1") is None


def test_registration_rolls_back_on_failed_head_write(acquisition):
    store, principal, first, _ = acquisition

    def fail_head(_connection, _cursor, statement, _parameters, _context, _executemany):
        if statement.startswith("INSERT INTO artifacts.source_heads"):
            raise RuntimeError("injected_head_failure")

    event.listen(store.engine, "before_cursor_execute", fail_head)
    try:
        with pytest.raises(RuntimeError, match="injected_head_failure"):
            store.register(principal, first, SourceDocument(first.reference, DATA))
    finally:
        event.remove(store.engine, "before_cursor_execute", fail_head)
    assert store.history(principal, "source", "r1") is None
    store.register(principal, first, SourceDocument(first.reference, DATA))


def test_scope_permissions_and_historical_immutability(acquisition):
    store, principal, first, e = acquisition
    source = SourceDocument(first.reference, DATA)
    with pytest.raises(UploadError, match="access_denied"):
        store.register(e.principal, first, source)
    foreign = replace(principal, scope=principal.scope.model_copy(update={"project_id": "foreign"}))
    with pytest.raises(ProvenanceError, match="source_scope_mismatch"):
        store.register(foreign, first, source)
    store.register(principal, first, source)
    assert store.history(foreign, "source", "r1") is None
    for statement in ("UPDATE artifacts.source_revisions SET canonical_bytes=decode('00','hex') WHERE false",
                      "DELETE FROM artifacts.conversion_traces WHERE false"):
        with pytest.raises(DBAPIError) as error, store.engine.begin() as connection:
            connection.execute(text(statement))
        assert error.value.orig.sqlstate == "42501"
