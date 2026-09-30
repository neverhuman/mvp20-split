"""Bounded command JSON profile; distinct from schema/artifact publication hashing."""

import hashlib
import json
import math
from dataclasses import dataclass

from amphora_contracts_core import WireModel
from pydantic import ValidationError

from .models import CommandIdentity

MAX_BYTES = 262144
MAX_DEPTH = 64
MAX_INTEGER = 9007199254740991
NUMERIC_ENCODING = "amphora-command-v2"


class CommandEncodingError(ValueError):
    """Reason code only: never reflect private input in public parse errors."""


def _integer(value: str) -> int:
    if len(value.lstrip("-")) > 16:
        raise CommandEncodingError("unsafe_integer")
    result = int(value)
    if abs(result) > MAX_INTEGER:
        raise CommandEncodingError("unsafe_integer")
    return result


def _reject_number(value: str):
    raise CommandEncodingError("non_integer_number")


class _NumberToken(str):
    """Defer float interpretation until the explicit envelope profile is known."""


def _finite_number(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise CommandEncodingError("non_finite_number")
    if result == 0:
        if any(char in "123456789" for char in value.lower().split("e")[0]):
            raise CommandEncodingError("number_underflow")
        return 0.0
    return result


def _normalize_numbers(value):
    if isinstance(value, _NumberToken):
        return _finite_number(value)
    if type(value) is float:
        return 0.0 if value == 0 else value
    if type(value) is dict:
        return {key: _normalize_numbers(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_normalize_numbers(item) for item in value]
    return value


def _object(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            raise CommandEncodingError("duplicate_key")
        output[key] = value
    return output


def _check_depth(text: str):
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise CommandEncodingError("too_deep")
        elif char in "]}":
            depth -= 1


def _check_value(value, depth=0, *, numeric=False):
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if abs(value) > MAX_INTEGER:
            raise CommandEncodingError("unsafe_integer")
    elif type(value) is float and numeric:
        if not math.isfinite(value):
            raise CommandEncodingError("non_finite_number")
    elif type(value) is str:
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise CommandEncodingError("invalid_unicode")
    elif type(value) in (dict, list, tuple):
        if depth >= MAX_DEPTH:
            raise CommandEncodingError("too_deep")
        if type(value) is dict:
            for key, item in value.items():
                if type(key) is not str:
                    raise CommandEncodingError("non_string_key")
                _check_value(key)
                _check_value(item, depth + 1, numeric=numeric)
        else:
            for item in value:
                _check_value(item, depth + 1, numeric=numeric)
    else:
        raise CommandEncodingError("unsupported_value")


def _encoded(value) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


@dataclass(frozen=True, slots=True)
class CanonicalCommand:
    """Validated snapshot of a command, with no mutable payload retained.

    Use parse at untrusted boundaries. The handler chooses a registered payload
    model for the command family and authenticates identity independently.
    """

    identity: CommandIdentity
    canonical_bytes: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes).hexdigest()

    @property
    def profile(self) -> str:
        return json.loads(self.canonical_bytes).get("encoding", "amphora-command-v1")

    @classmethod
    def for_family(cls, raw: str | bytes, family: str,
                   payload_model: type[WireModel], *, allow_numeric=False) -> "CanonicalCommand":
        command = cls.parse(raw, payload_model, allow_numeric=allow_numeric)
        if command.identity.command_family != family:
            raise CommandEncodingError("family_mismatch")
        return command

    @classmethod
    def parse(cls, raw: str | bytes, payload_model: type[WireModel], *, allow_numeric=False) -> "CanonicalCommand":
        if not isinstance(payload_model, type) or not issubclass(payload_model, WireModel):
            raise TypeError("payload_model must be a registered WireModel class")
        try:
            data = raw.encode("utf-8") if isinstance(raw, str) else raw
            if not isinstance(data, bytes):
                raise CommandEncodingError("invalid_input_type")
            if len(data) > MAX_BYTES:
                raise CommandEncodingError("too_large")
            if data.startswith(b"\xef\xbb\xbf"):
                raise CommandEncodingError("bom_forbidden")
            text = data.decode("utf-8")
        except UnicodeError as error:
            raise CommandEncodingError("invalid_unicode") from error
        _check_depth(text)
        try:
            value = json.loads(text, object_pairs_hook=_object, parse_int=_integer,
                               parse_float=_NumberToken if allow_numeric else _reject_number, parse_constant=_reject_number)
        except json.JSONDecodeError as error:
            raise CommandEncodingError("invalid_json") from error
        if allow_numeric and type(value) is dict and "encoding" not in value:
            # An opted-in route still preserves the exact legacy parser/default/hash behavior.
            return cls.parse(raw, payload_model)
        numeric = allow_numeric and type(value) is dict and value.get("encoding") == NUMERIC_ENCODING
        if allow_numeric and not numeric:
            raise CommandEncodingError("invalid_encoding")
        if numeric:
            value = _normalize_numbers(value)
        _check_value(value, numeric=numeric)
        if type(value) is not dict or set(value) != ({"identity", "payload", "encoding"} if numeric else {"identity", "payload"}):
            raise CommandEncodingError("invalid_envelope")
        if type(value["payload"]) is not dict:
            raise CommandEncodingError("invalid_payload")
        try:
            identity = CommandIdentity.model_validate_json(_encoded(value["identity"]))
            payload = payload_model.model_validate_json(_encoded(value["payload"]))
        except ValidationError as error:
            raise CommandEncodingError("schema_invalid") from error
        normalized = {"identity": identity.model_dump(), "payload": payload.model_dump()}
        if numeric:
            _check_value(normalized, numeric=True)
            normalized = _normalize_numbers({"encoding": NUMERIC_ENCODING, **normalized})
        _check_value(normalized, numeric=numeric)
        encoded = _encoded(normalized)
        if len(encoded) > MAX_BYTES:
            raise CommandEncodingError("too_large")
        return cls(identity, encoded)
