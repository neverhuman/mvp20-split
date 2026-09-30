"""Independent JSON consumers share shape rules, not owner authority."""

import copy
import hashlib
import json

import pytest
from amphora_contracts_evidence import ConversionTrace, SourceRevision, SourceSpan
from jsonschema import Draft202012Validator
from pydantic import ValidationError


def example():
    scope = {"tenant_id": "synthetic", "project_id": "acquisition"}
    digest = hashlib.sha256(b"mass: unknown").hexdigest()
    schema = {"schema_id": "raw-document", "version": "1", "sha256": "a" * 64}
    raw = {"artifact_id": "raw-1", "scope": scope, "sha256": digest,
           "media_type": "text/plain", "schema_ref": schema, "size_bytes": 13}
    source = {"scope": scope, "source_id": "document", "revision_id": "revision-1", "raw": raw}
    span = {"source": source, "unit": "byte", "start": 0, "end": 13, "sha256": digest}
    output = {**raw, "artifact_id": "output-1", "media_type": "application/json"}
    return {
        "wire_version": "1", "scope": scope, "trace_id": "trace-1", "source": source,
        "source_schema": schema, "target_schema": schema, "converter_id": "document-parser",
        "converter_version": "1", "configuration_sha256": "b" * 64,
        "transforms": [{"transform_id": "parse", "version": "1",
                        "configuration_sha256": "b" * 64, "kind": "deterministic"}],
        "output": output,
        "fields": [{"target_path": "/mass", "origin": "missing", "spans": [span], "step_indices": [0]}],
        "warnings": [{"code": "missing_value", "target_path": "/mass"}],
        "disposition": "unresolved",
    }


def assert_shared_valid(model, value):
    raw = json.dumps(value)
    parsed = model.model_validate_json(raw)
    for mode in ("validation", "serialization"):
        schema = model.model_json_schema(mode=mode)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(json.loads(parsed.model_dump_json()))
    assert json.loads(parsed.model_dump_json()) == value
    return parsed


def test_missing_and_inferred_values_remain_explicit_without_acceptance():
    trace = example()
    parsed = assert_shared_valid(ConversionTrace, trace)
    assert parsed.fields[0].origin == "missing"
    assert isinstance(parsed.fields, tuple)
    with pytest.raises(ValidationError):
        parsed.trace_id = "changed"
    trace["fields"][0]["origin"] = "inferred"
    trace["transforms"][0]["kind"] = "inference"
    trace["disposition"] = "quarantined"
    assert_shared_valid(ConversionTrace, trace)


@pytest.mark.parametrize("mutation", [
    lambda x: x.update(scientifically_accepted=True),
    lambda x: x.update(wire_version="2"),
    lambda x: x.update(disposition="accepted"),
    lambda x: x.update(transforms=[]),
    lambda x: x.update(fields=x["fields"] * 257),
    lambda x: x["fields"][0].update(origin="confident"),
    lambda x: x["fields"][0].update(step_indices=[32]),
    lambda x: x["fields"][0].update(target_path="mass"),
    lambda x: x["source"]["raw"].update(size_bytes=True),
    lambda x: x["fields"][0]["spans"][0].update(start=-1),
    lambda x: x["fields"][0]["spans"][0].update(unit="character"),
    lambda x: x["fields"][0]["spans"][0].update(end="13"),
    lambda x: x["fields"][0]["spans"][0].update(end=9007199254740992),
])
def test_invalid_shapes_rejected_by_python_and_independent_schema(mutation):
    value = copy.deepcopy(example())
    mutation(value)
    with pytest.raises(ValidationError):
        ConversionTrace.model_validate_json(json.dumps(value))
    assert list(Draft202012Validator(ConversionTrace.model_json_schema()).iter_errors(value))


def test_source_revision_and_byte_span_roundtrip():
    trace = example()
    assert_shared_valid(SourceSpan, trace["fields"][0]["spans"][0])
    value = {
        "wire_version": "1", "reference": trace["source"],
        "delivery": {"issuer_id": "fixture", "delivery_id": "delivery-1"},
        "method": {"connector_id": "plain-document", "connector_version": "1",
                   "configuration_sha256": "b" * 64, "format": "utf8_document"},
        "rights": {"scope": trace["scope"], "rights_id": "fixture-rights", "revision": 1},
        "supersedes": None, "completeness": "unknown",
    }
    assert_shared_valid(SourceRevision, value)
