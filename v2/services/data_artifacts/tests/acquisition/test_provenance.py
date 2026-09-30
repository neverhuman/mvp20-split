"""Owned oracles: Unicode byte provenance and immutable trace fingerprints."""

import copy
import hashlib
import json

import pytest
from amphora_contracts_evidence import ConversionTrace, SourceRevisionRef, SourceSpan
from amphora_data_artifacts.acquisition.provenance import (
    MAX_PROVENANCE_BYTES,
    ProvenanceError,
    SourceDocument,
    TraceDocument,
)

RAW = "μg: 12\n".encode()
OUTPUT = b'{"mass":"12","unit":"ug"}'


def digest(value):
    return hashlib.sha256(value).hexdigest()


def record():
    scope = {"tenant_id": "test", "project_id": "source"}
    schema = {"schema_id": "fixture", "version": "1", "sha256": "a" * 64}
    raw = {"artifact_id": "raw", "scope": scope, "sha256": digest(RAW),
           "media_type": "text/plain", "schema_ref": schema, "size_bytes": len(RAW)}
    source = {"scope": scope, "source_id": "lab", "revision_id": "r1", "raw": raw}
    span = {"source": source, "unit": "byte", "start": 0, "end": 3, "sha256": digest(RAW[:3])}
    return {
        "wire_version": "1", "scope": scope, "trace_id": "t1", "source": source,
        "source_schema": schema, "target_schema": schema, "converter_id": "fixture",
        "converter_version": "1", "configuration_sha256": "b" * 64,
        "transforms": [{"transform_id": "copy", "version": "1",
                        "configuration_sha256": "b" * 64, "kind": "deterministic"}],
        "output": {**raw, "artifact_id": "output", "sha256": digest(OUTPUT),
                   "media_type": "application/json", "size_bytes": len(OUTPUT)},
        "fields": [{"target_path": "/unit", "origin": "copied", "spans": [span], "step_indices": [0]}],
        "warnings": [], "disposition": "normalized",
    }


def parse(value):
    return ConversionTrace.model_validate_json(json.dumps(value))


def source():
    return SourceDocument(parse(record()).source, RAW)


def test_utf8_span_uses_bytes_and_rejects_character_offset_confusion():
    document = source()
    span = parse(record()).fields[0].spans[0]
    assert document.extract(span) == "μg".encode()
    with pytest.raises(ProvenanceError, match="span_digest_mismatch"):
        document.extract(span.model_copy(update={"end": 2}))
    empty = span.model_copy(update={"start": 1, "end": 1, "sha256": digest(b"")})
    assert document.extract(empty) == b""


def test_retry_fingerprint_is_stable_and_transform_changes_are_distinct():
    a = TraceDocument.verify(parse(record()), source(), OUTPUT)
    b = TraceDocument.verify(ConversionTrace.model_validate_json(a.canonical_bytes), source(), OUTPUT)
    assert a.reference() == b.reference()
    assert a.canonical_bytes == b.canonical_bytes
    changed = record()
    changed["transforms"][0]["version"] = "2"
    c = TraceDocument.verify(parse(changed), source(), OUTPUT)
    assert a.reference().trace_id == c.reference().trace_id
    assert a.reference().sha256 != c.reference().sha256  # Store must reject this ID collision.


@pytest.mark.parametrize(("mutation", "code"), [
    (lambda x: x.update(scope={"tenant_id": "other", "project_id": "source"}), "trace_scope_mismatch"),
    (lambda x: x["source"].update(revision_id="r2"), "trace_source_mismatch"),
    (lambda x: x.update(source_schema={"schema_id": "wrong", "version": "1", "sha256": "a"*64}),
     "source_schema_mismatch"),
    (lambda x: x.update(target_schema={"schema_id": "wrong", "version": "1", "sha256": "a"*64}),
     "target_schema_mismatch"),
    (lambda x: x["output"].update(scope={"tenant_id": "other", "project_id": "source"}),
     "artifact_scope_mismatch"),
    (lambda x: x["output"].update(sha256="0"*64), "content_digest_mismatch"),
    (lambda x: x["output"].update(size_bytes=1), "content_size_mismatch"),
    (lambda x: x["fields"].append(copy.deepcopy(x["fields"][0])), "duplicate_field_path"),
    (lambda x: x["fields"][0].update(step_indices=[0, 0]), "duplicate_step_reference"),
    (lambda x: x["fields"][0].update(step_indices=[1]), "unknown_step"),
    (lambda x: x["fields"][0].update(step_indices=[]), "origin_step_mismatch"),
    (lambda x: x["fields"][0].update(spans=[]), "missing_source_span"),
    (lambda x: x["fields"][0].update(origin="inferred"), "origin_step_mismatch"),
    (lambda x: x["fields"][0].update(origin="missing"), "unresolved_field_disposition"),
    (lambda x: x["transforms"][0].update(kind="inference"), "origin_step_mismatch"),
    (lambda x: x["fields"][0]["spans"][0].update(end=100), "span_bounds"),
    (lambda x: x["fields"][0]["spans"][0].update(start=4), "span_bounds"),
    (lambda x: x["fields"][0]["spans"][0]["source"].update(revision_id="wrong"), "span_source_mismatch"),
])
def test_cross_record_errors_are_safe_codes(mutation, code):
    value = json.loads(json.dumps(record()))
    mutation(value)
    with pytest.raises(ProvenanceError) as error:
        TraceDocument.verify(parse(value), source(), OUTPUT)
    assert str(error.value) == code


@pytest.mark.parametrize("origin", ["missing", "inferred"])
def test_unresolved_origins_cannot_be_normalized(origin):
    value = record()
    value["fields"][0].update(origin=origin, spans=[])
    if origin == "inferred":
        value["transforms"][0]["kind"] = "inference"
    with pytest.raises(ProvenanceError, match="unresolved_field_disposition"):
        TraceDocument.verify(parse(value), source(), OUTPUT)
    value["disposition"] = "quarantined"
    assert TraceDocument.verify(parse(value), source(), OUTPUT).trace.fields[0].origin == origin


def test_source_limit_and_mutable_content_are_rejected():
    ref = source().reference
    with pytest.raises(ProvenanceError, match="content_limit"):
        SourceDocument(ref, b"x" * (MAX_PROVENANCE_BYTES + 1))
    with pytest.raises(ProvenanceError, match="content_requires_bytes"):
        SourceDocument(ref, bytearray(RAW))


def test_source_reference_cannot_hide_foreign_artifact():
    value = copy.deepcopy(record()["source"])
    value["raw"]["scope"]["tenant_id"] = "foreign"
    value["scope"] = {"tenant_id": "test", "project_id": "source"}
    ref = SourceRevisionRef.model_validate_json(json.dumps(value))
    with pytest.raises(ProvenanceError, match="artifact_scope_mismatch"):
        SourceDocument(ref, RAW)


def test_span_public_json_roundtrip_preserves_exact_reference():
    span = parse(record()).fields[0].spans[0]
    assert source().extract(SourceSpan.model_validate_json(span.model_dump_json())) == RAW[:3]
