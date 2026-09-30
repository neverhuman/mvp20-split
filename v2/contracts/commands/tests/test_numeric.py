import json
from pathlib import Path
from typing import Annotated

import pytest
from amphora_contracts_commands import NUMERIC_ENCODING, CanonicalCommand, CommandEncodingError
from amphora_contracts_core import WireModel
from pydantic import Field

from .test_canonical import IDENTITY, Payload


class NumericPayload(WireModel):
    amount: Annotated[float, Field(ge=-1e100, le=1e100)]
    count: int = 1


def raw(payload, **changes):
    return json.dumps({"encoding": NUMERIC_ENCODING, "identity": IDENTITY, "payload": payload, **changes})


@pytest.mark.parametrize("case", json.loads((Path(__file__).parent / "fixtures/canonical_v2.json").read_text()), ids=lambda case: case["name"])
def test_numeric_fixed_vectors_and_canonical_replay(case):
    command = CanonicalCommand.for_family(case["input"], "test.operation", NumericPayload, allow_numeric=True)
    assert command.canonical_bytes == case["canonical"].encode("ascii")
    assert command.sha256 == case["sha256"]
    assert CanonicalCommand.parse(command.canonical_bytes, NumericPayload, allow_numeric=True) == command
    with pytest.raises(CommandEncodingError):
        CanonicalCommand.parse(case["input"], NumericPayload)


@pytest.mark.parametrize("case", json.loads((Path(__file__).parent / "fixtures/canonical_v1.json").read_text()), ids=lambda case: case["name"])
def test_opted_in_owner_preserves_legacy_vectors(case):
    command = CanonicalCommand.parse(case["input"], Payload, allow_numeric=True)
    assert command.canonical_bytes == case["canonical"].encode("ascii")
    assert command.sha256 == case["sha256"]


@pytest.mark.parametrize("token,reason", [("1e309", "non_finite_number"), ("-1e309", "non_finite_number"),
    ("1e-9999", "number_underflow"), ("NaN", "non_integer_number"), ("Infinity", "non_integer_number"),
    ("9007199254740992", "unsafe_integer"), ("1e101", "schema_invalid")])
def test_numeric_rejections(token, reason):
    value = raw({"amount": "TOKEN"}).replace('"TOKEN"', token)
    with pytest.raises(CommandEncodingError, match=reason):
        CanonicalCommand.parse(value, NumericPayload, allow_numeric=True)


def test_profile_identity_defaults_and_safe_integer_separation():
    integer = CanonicalCommand.parse(raw({"amount": 1}), NumericPayload, allow_numeric=True)
    decimal = CanonicalCommand.parse(raw({"amount": 1.0}), NumericPayload, allow_numeric=True)
    assert integer == decimal
    assert CanonicalCommand.parse(raw({"amount": -0.0}), NumericPayload, allow_numeric=True) == CanonicalCommand.parse(raw({"amount": 0.0}), NumericPayload, allow_numeric=True)
    legacy = json.dumps({"identity": IDENTITY, "payload": {"count": 1}})
    old = CanonicalCommand.parse(legacy, Payload)
    new = CanonicalCommand.parse(raw({"count": 1}), Payload, allow_numeric=True)
    assert old.identity == new.identity and old.sha256 != new.sha256
    for value in [raw({"amount": 1}, encoding="unknown"), raw({"amount": 1}, extra=True),
                  raw({"amount": 1, "count": 1.0}), raw({"amount": 1}).replace('"encoding":', '"encoding":"duplicate","encoding":')]:
        with pytest.raises(CommandEncodingError):
            CanonicalCommand.parse(value, NumericPayload, allow_numeric=True)
    with pytest.raises(CommandEncodingError, match="family_mismatch"):
        CanonicalCommand.for_family(raw({"amount": 1}), "other", NumericPayload, allow_numeric=True)
    with pytest.raises(CommandEncodingError, match="unsupported_value"):
        CanonicalCommand.parse(json.dumps({"identity": IDENTITY, "payload": {"amount": 1}}), NumericPayload, allow_numeric=True)


def test_numeric_profile_retains_unicode_size_and_depth_bounds():
    class NumericDefault(Payload):
        amount: float = -0.0

    command = CanonicalCommand.parse(raw({}), NumericDefault, allow_numeric=True)
    assert json.loads(command.canonical_bytes)["payload"]["amount"] == 0.0
    for value, reason in [(raw({"text": "\ud800"}), "invalid_unicode"),
                          (raw({"text": "a" * 262144}), "too_large"),
                          (raw({"text": "\u00e9" * 45000}), "too_large"),
                          ('[' * 65 + '0' + ']' * 65, "too_deep")]:
        with pytest.raises(CommandEncodingError, match=reason):
            CanonicalCommand.parse(value, NumericDefault, allow_numeric=True)


def test_default_materialization_cannot_bypass_finite_or_canonical_byte_bounds():
    class InfiniteDefault(WireModel):
        amount: float = float("inf")

    class LargeDefault(WireModel):
        text: str = "\u00e9" * 45000

    with pytest.raises(CommandEncodingError, match="non_finite_number|schema_invalid"):
        CanonicalCommand.parse(raw({}), InfiniteDefault, allow_numeric=True)
    with pytest.raises(CommandEncodingError, match="too_large"):
        CanonicalCommand.parse(raw({}), LargeDefault, allow_numeric=True)


@pytest.mark.parametrize("token", ["1.25", "1e309", "1e-9999"])
def test_opted_in_routes_do_not_reinterpret_unmarked_numeric_input(token):
    value = json.dumps({"identity": IDENTITY, "payload": {"amount": "TOKEN"}}).replace('"TOKEN"', token)
    with pytest.raises(CommandEncodingError, match="non_integer_number"):
        CanonicalCommand.parse(value, NumericPayload, allow_numeric=True)
