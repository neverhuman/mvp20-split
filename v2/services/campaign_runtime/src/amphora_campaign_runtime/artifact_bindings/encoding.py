"""Bounded JSON preserving decimal values across Artifact and graph boundaries."""

import json
from decimal import Decimal

from ..coordinator.values import ensure


def encoded(value, *, depth=0):
    ensure(depth <= 64, "binding_json_depth")
    if isinstance(value, Decimal):
        ensure(value.is_finite() and value.copy_abs() <= Decimal("1e100") and value.as_tuple().exponent >= -324,
               "binding_decimal_range")
        return format(value, "f")
    if isinstance(value, dict):
        ensure(all(isinstance(key, str) for key in value), "binding_json_keys")
        return "{" + ",".join(json.dumps(key, ensure_ascii=True) + ":" + encoded(value[key], depth=depth + 1)
                              for key in sorted(value)) + "}"
    if isinstance(value, (tuple, list)):
        return "[" + ",".join(encoded(item, depth=depth + 1) for item in value) + "]"
    ensure(value is None or type(value) in {str, int, bool}, "binding_json_value")
    return json.dumps(value, ensure_ascii=True, allow_nan=False)


def payload(value):
    return encoded(value).encode("ascii")
