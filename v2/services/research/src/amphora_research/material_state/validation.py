"""Bounded material-state primitives; no cross-owner reads or inferred scientific identity."""
from amphora_contracts_core import Identifier
from pydantic import TypeAdapter, ValidationError

IDENTIFIER = TypeAdapter(Identifier)


class MaterialStateError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise MaterialStateError(reason)


def identifier(value):
    try:
        IDENTIFIER.validate_python(value, strict=True)
    except ValidationError as error:
        raise MaterialStateError("invalid_state_identifier") from error


def bounded_tuple(value, maximum, reason):
    require(type(value) is tuple and len(value) <= maximum, reason)
