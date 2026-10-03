"""Bounded synthesis identity and collection invariants."""
from amphora_contracts_core import Identifier
from pydantic import TypeAdapter, ValidationError

IDENTIFIER = TypeAdapter(Identifier)


class SynthesisError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise SynthesisError(reason)


def identifier(value):
    try:
        IDENTIFIER.validate_python(value,strict=True)
    except ValidationError as error:
        raise SynthesisError("invalid_synthesis_identifier") from error


def bounded(items,kind,limit,reason):
    require(type(items) is tuple and len(items) <= limit,reason)
    require(all(type(item) is kind for item in items),reason)


def names(items,limit=64):
    bounded(items,str,limit,"synthesis_reason_bound")
    for item in items:
        identifier(item)
    require(len(set(items)) == len(items),"duplicate_synthesis_reason")
