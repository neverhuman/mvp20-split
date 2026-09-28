"""Offline, hash-bound projection types; references cannot initiate remote retrieval."""

import hashlib
import json
from dataclasses import FrozenInstanceError

import pytest
from amphora_campaign_runtime.compiler import CompilationError, PinnedSchema, SchemaCatalog, SchemaIdentity
from amphora_campaign_runtime.compiler.shapes import ScalarShape


def pinned(value):
    body = value if isinstance(value, bytes) else json.dumps(value).encode()
    return PinnedSchema(SchemaIdentity("test.schema", "1", hashlib.sha256(body).hexdigest()), body)


def test_local_schema_projection_and_annotations():
    schema = pinned({"type": "object", "properties": {"values": {"type": "array", "maxItems": 2,
                     "items": {"$ref": "#/$defs/scalar"}}},
                     "$defs": {"scalar": {"type": "number", "x-amphora-unit": "g/mol"}}})
    assert schema.project(("values", 0), "1", "node") == ScalarShape("number", "g/mol")
    with pytest.raises(CompilationError, match="projection_out_of_bounds"):
        schema.project(("values", 2), "1", "node")


@pytest.mark.parametrize("value,code", [
    (b'{"type":"integer","type":"number"}', "invalid_schema_document"),
    (b'{"minimum":NaN}', "invalid_schema_document"),
    (b'{"minimum":1e999}', "invalid_schema_document"),
    (b'[]', "invalid_schema_document"),
    ({"type": "unknown"}, "invalid_schema_document"),
    ({"$ref": "https://example.invalid/schema"}, "external_schema_reference"),
    ({"$id": "https://example.invalid/schema"}, "unsupported_schema_reference"),
    ({"$dynamicRef": "#node"}, "unsupported_schema_reference"),
    ({"$schema": "https://json-schema.org/draft-07/schema"}, "unsupported_schema_dialect"),
    ({"$ref": "#/$defs/missing"}, "unresolved_schema_reference"),
    ({"$ref": "#/examples/0", "examples": [{"type": "integer"}]}, "invalid_schema_reference_target"),
    ({"$ref": "#/prefixItems/-1", "prefixItems": [{"type": "integer"}]}, "unresolved_schema_reference"),
    ({"$ref": "#/prefixItems/00", "prefixItems": [{"type": "integer"}]}, "unresolved_schema_reference"),
])
def test_rejected_schema_documents(value, code):
    with pytest.raises(CompilationError, match=code):
        pinned(value)


@pytest.mark.parametrize("value,path,code", [
    ({"$ref": "#"}, (), "cyclic_projection_reference"),
    ({"type": ["number", "null"]}, (), "projection_not_scalar"),
    ({"anyOf": [{"type": "integer"}]}, (), "unsupported_projection_schema"),
    ({"type": "object", "properties": {}}, ("missing",), "unknown_projection_property"),
    ({"type": "integer"}, (0,), "projection_not_array"),
    ({"type": "array"}, (0,), "unsupported_projection_schema"),
    ({"type": "string", "x-amphora-unit": "g"}, (), "invalid_projection_unit"),
    ({"$ref": "#/$defs/n", "minimum": 0, "$defs": {"n": {"type": "integer"}}}, (), "unsupported_projection_reference"),
])
def test_ambiguous_or_missing_projection_is_rejected(value, path, code):
    schema = pinned(value)
    with pytest.raises(CompilationError, match=code):
        schema.project(path, "1", "node")


def test_hash_and_catalog_identity_are_exact():
    schema = pinned({"type": "number"})
    assert SchemaCatalog([schema]).require(schema.identity, "node") is schema
    with pytest.raises(CompilationError, match="duplicate_schema_identity"):
        SchemaCatalog([schema, schema])
    with pytest.raises(CompilationError, match="schema_digest_mismatch"):
        PinnedSchema(schema.identity, b'{}')
    with pytest.raises(CompilationError, match="unknown_schema_pin"):
        SchemaCatalog([]).require(schema.identity, "node")
    with pytest.raises(FrozenInstanceError):
        schema.identity = None
    with pytest.raises(TypeError):
        schema._document["type"] = "integer"
