"""Hash-bound owner validation without tool implementation imports."""

import hashlib
import json

import pytest
from amphora_contracts_artifacts import ContentDescriptor
from amphora_data_artifacts.publication.model import ContentPolicy, UploadError
from amphora_data_artifacts.publication.schemas import (
    JsonSchemaRule,
    configured_profiles,
)
from jsonschema.exceptions import SchemaError


def profile(schema):
    document = json.dumps(schema).encode()
    identity = ("application/json", "example.output", "1", hashlib.sha256(document).hexdigest())
    rule = JsonSchemaRule(identity, document)
    return ContentPolicy(frozenset({identity}), (rule,))


def descriptor(policy, payload):
    media, identifier, version, digest = next(iter(policy.allowed))
    return ContentDescriptor.model_validate_json(json.dumps({"sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload), "media_type": media,
        "schema_ref": {"schema_id": identifier, "version": version, "sha256": digest}}))


@pytest.mark.parametrize("payload,valid", [
    (b'{"value":-2.5}', True), (b'{"value":0}', True), (b'{"value":"2"}', False),
    (b'{"value":true}', False), (b'{}', False), (b'{"value":1,"extra":2}', False),
    (b'{"value":NaN}', False), (b'{"value":1e999}', False), (b'{"value":1,"value":2}', False),
])
def test_exact_typed_payload(payload, valid):
    policy = profile({"type": "object", "properties": {"value": {"type": "number"}},
        "required": ["value"], "additionalProperties": False})
    if valid:
        policy.validate(descriptor(policy, payload), payload)
    else:
        with pytest.raises(UploadError, match="content_schema_mismatch"):
            policy.validate(descriptor(policy, payload), payload)


def test_local_definitions_formats_and_non_object_payloads():
    policy = profile({"$defs": {"stamp": {"type": "string", "format": "date-time"}},
        "type": "array", "items": {"$ref": "#/$defs/stamp"}})
    payload = b'["2026-09-28T15:00:00Z"]'
    policy.validate(descriptor(policy, payload), payload)
    invalid = b'["not-a-date"]'
    with pytest.raises(UploadError, match="content_schema_mismatch"):
        policy.validate(descriptor(policy, invalid), invalid)
    profile({"type": "object", "properties": {"format": {"type": "string"}, "$id": {"type": "number"}},
             "examples": [{"$ref": "https://ordinary-data.example"}]})


@pytest.mark.parametrize("schema", [
    {"$ref": "https://untrusted.example/schema"}, {"$ref": "file:///private/schema"},
    {"$ref": "#missing"}, {"$ref": "#/$defs/missing"}, {"$id": "https://untrusted.example/"},
    {"$dynamicRef": "#anything"}, {"$schema": "http://json-schema.org/draft-07/schema#"},
    {"type": "not-a-type"}, {"format": "invented"},
    {"properties": {"value": {"$ref": "https://untrusted.example/schema"}}},
    {"$ref": "#/examples/0", "examples": [{"$ref": "https://untrusted.example/schema"}]},
])
def test_unsupported_or_external_schema_fails_before_serving(schema):
    with pytest.raises((ValueError, SchemaError)):
        profile(schema)


def test_hash_size_duplicates_and_configuration(tmp_path):
    document = b'{"type":"integer"}'
    path = tmp_path / "integer.json"
    path.write_bytes(document)
    entry = {"media_type": "application/json", "schema_id": "integer", "version": "1",
             "sha256": hashlib.sha256(document).hexdigest(), "schema_path": "integer.json"}
    policy = ContentPolicy(*configured_profiles([entry], tmp_path))
    policy.validate(descriptor(policy, b"12"), b"12")
    with pytest.raises(ValueError, match="Duplicate"):
        configured_profiles([entry, entry], tmp_path)
    with pytest.raises(ValueError, match="configuration"):
        configured_profiles([{**entry, "unknown": 1}], tmp_path)
    path.write_bytes(b'{"type":"string"}')
    with pytest.raises(ValueError, match="identity"):
        configured_profiles([entry], tmp_path)
    large = b" " * 65537
    with pytest.raises(ValueError, match="size"):
        JsonSchemaRule(("application/json", "large", "1", hashlib.sha256(large).hexdigest()), large)
    with pytest.raises(ValueError, match="Duplicate"):
        ContentPolicy(policy.allowed, policy.rules * 2)


@pytest.mark.postgres
def test_actual_publication_uses_configured_schema(upload_env):
    e = upload_env
    policy = profile({"type": "object", "properties": {"value": {"type": "number"}},
                      "required": ["value"], "additionalProperties": False})
    e.uploads.policy = policy
    for index, payload in enumerate((b'{"value":3}', b'{"value":"wrong"}')):
        content = descriptor(policy, payload)
        identity = {"actor_id": "worker", "scope": e.principal.scope.model_dump(),
                    "command_id": f"typed-{index}", "command_family": "artifacts.begin_upload"}
        begin = e.client.post("/v1/uploads", json={"identity": identity,
            "payload": {"content": content.model_dump()}}, headers=e.headers)
        assert begin.status_code == 200
        upload = begin.json()["upload_id"]
        assert e.client.put(f"/v1/uploads/{upload}/content", content=payload, headers=e.headers).status_code == 200
        identity["command_family"] = "artifacts.finalize"
        final = e.client.post("/v1/artifacts/finalize", json={"identity": identity,
            "payload": {"upload_id": upload, "content": content.model_dump()}}, headers=e.headers)
        assert final.status_code == (200 if index == 0 else 409)
        if index:
            assert final.json()["reason_code"] == "content_schema_mismatch"


def test_exact_canonical_root_identity_uses_original_bytes_and_local_references():
    schema = {"$id": "urn:amphora:example.output:1:validation", "type": "object",
              "properties": {"value": {"$ref": "#/$defs/n"}}, "required": ["value"],
              "$defs": {"n": {"type": "integer", "minimum": 0}}}
    policy = profile(schema)
    assert policy.rules[0].document == json.dumps(schema).encode()
    payload = b'{"value":2}'
    policy.validate(descriptor(policy, payload), payload)
    invalid = b'{"value":-1}'
    with pytest.raises(UploadError, match="content_schema_mismatch"):
        policy.validate(descriptor(policy, invalid), invalid)


@pytest.mark.parametrize("schema", [
    {"$id": "urn:amphora:wrong:1:validation"},
    {"$id": "urn:amphora:example.output:2:validation"},
    {"$id": "urn:amphora:example.output:1:serialization"},
    {"type": "object", "properties": {"n": {"$id": "urn:amphora:example.output:1:validation"}}},
    {"$id": "urn:amphora:example.output:1:validation", "$ref": "https://example.invalid/schema"},
    {"$id": "urn:amphora:example.output:1:validation", "$anchor": "local"},
])
def test_canonical_root_does_not_enable_other_resources(schema):
    with pytest.raises(ValueError):
        profile(schema)
