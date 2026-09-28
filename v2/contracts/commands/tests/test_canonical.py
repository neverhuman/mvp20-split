import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from amphora_contracts_commands import CanonicalCommand, CommandEncodingError, CommandIdentity
from amphora_contracts_core import WireModel
from jsonschema import Draft202012Validator


class Payload(WireModel):
    text: str = ""
    count: int = 1
    enabled: bool = True
    labels: tuple[str, ...] = ()
    note: str | None = None


IDENTITY = {"actor_id": "worker-1", "command_family": "test.operation", "command_id": "cmd-1",
            "scope": {"tenant_id": "local", "project_id": "demo"}}


def envelope(payload=None):
    return {"identity": IDENTITY, "payload": {} if payload is None else payload}


def parse(payload=None):
    return CanonicalCommand.parse(json.dumps(envelope(payload)), Payload)


@pytest.mark.parametrize("case", json.loads(
    (Path(__file__).parent / "fixtures/canonical_v1.json").read_text(encoding="utf-8")
), ids=lambda case: case["name"])
def test_fixed_interchange_vectors(case):
    value = CanonicalCommand.parse(case["input"], Payload)
    assert value.canonical_bytes == case["canonical"].encode("ascii")
    assert value.sha256 == case["sha256"]
    Draft202012Validator(CommandIdentity.model_json_schema()).validate(
        json.loads(value.canonical_bytes)["identity"]
    )


def test_equivalent_inputs_and_immutable_snapshot():
    defaults = Payload().model_dump(mode="json")
    expected = parse()
    alternate = envelope(defaults)
    alternate["identity"] = {**IDENTITY, "schema_version": "1"}
    assert CanonicalCommand.parse(json.dumps(alternate, indent=3), Payload) == expected
    assert parse({"count": 2}).sha256 != expected.sha256
    alternate["payload"]["count"] = 12
    assert expected == parse()
    with pytest.raises(FrozenInstanceError):
        expected.canonical_bytes = b"changed"


@pytest.mark.parametrize("raw,reason", [
    ('{"identity":{},"identity":{},"payload":{}}', "duplicate_key"),
    ('{"identity":{},"payload":{"x":1,"x":2}}', "duplicate_key"),
    ('{"identity":{},"payload":{"x":1.0}}', "non_integer_number"),
    ('{"identity":{},"payload":{"x":1e2}}', "non_integer_number"),
    ('{"identity":{},"payload":{"x":NaN}}', "non_integer_number"),
    ('{"identity":{},"payload":{"x":Infinity}}', "non_integer_number"),
    ('{"identity":{},"payload":{"x":9007199254740992}}', "unsafe_integer"),
    ('{"identity":{},"payload":{"x":-9007199254740992}}', "unsafe_integer"),
    ('{"identity":{},"payload":{"x":999999999999999999999999}}', "unsafe_integer"),
    ('{"identity":{},"payload":{"x":"\\ud800"}}', "invalid_unicode"),
    ('{"identity":{},"payload":{"\\udfff":0}}', "invalid_unicode"),
    ('\ud800', "invalid_unicode"),
    (b'\xff', "invalid_unicode"),
    (b'\xef\xbb\xbf{}', "bom_forbidden"),
    ('{} trailing', "invalid_json"),
    ('[]', "invalid_envelope"),
    ('{"identity":{},"payload":{},"credentials":"secret"}', "invalid_envelope"),
    ('{"identity":{},"payload":[]}', "invalid_payload"),
    (json.dumps(envelope({"count": "SECRET"})), "schema_invalid"),
    (json.dumps(envelope({"unknown": "SECRET"})), "schema_invalid"),
    (123, "invalid_input_type"),
])
def test_profile_rejections_do_not_echo_input(raw, reason):
    with pytest.raises(CommandEncodingError) as error:
        CanonicalCommand.parse(raw, Payload)
    assert str(error.value) == reason


def test_boundaries_and_escaped_string_depth():
    assert parse({"count": 9007199254740991})
    assert parse({"count": -9007199254740991})
    assert parse({"text": '[{"\\' * 100})
    raw = json.dumps(envelope())
    assert CanonicalCommand.parse(raw + ' ' * (262144 - len(raw)), Payload)
    with pytest.raises(CommandEncodingError, match="too_large"):
        CanonicalCommand.parse(raw + ' ' * (262145 - len(raw)), Payload)
    with pytest.raises(CommandEncodingError, match="too_large"):
        parse({"text": '\u00e9' * 45000})


def test_depth_exact_boundary_and_schema_default_validation():
    class Nested(WireModel):
        child: "Nested | None" = None

    node = {}
    for _ in range(62):
        node = {"child": node}
    assert CanonicalCommand.parse(json.dumps(envelope(node)), Nested)
    with pytest.raises(CommandEncodingError, match="too_deep"):
        CanonicalCommand.parse(json.dumps(envelope({"child": node})), Nested)

    class BadDefault(WireModel):
        number: float = 1.0

    with pytest.raises(CommandEncodingError, match="unsupported_value"):
        CanonicalCommand.parse(json.dumps(envelope()), BadDefault)
    with pytest.raises(TypeError):
        CanonicalCommand.parse(json.dumps(envelope()), dict)


def test_unicode_normalization_is_not_silently_applied():
    assert parse({"text": "\u00e9"}).sha256 != parse({"text": "e\u0301"}).sha256
    assert parse({"text": "\U0001f600"})
