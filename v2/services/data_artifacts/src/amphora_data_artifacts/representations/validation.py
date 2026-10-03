"""Bounded semantic validation and versioned canonical identities."""

import hashlib
import json

from amphora_contracts_core import Digest, Identifier, SchemaRef, Scope
from pydantic import TypeAdapter, ValidationError

IDENTIFIER = TypeAdapter(Identifier)
DIGEST = TypeAdapter(Digest)


class RepresentationError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise RepresentationError(code)


def identifier(value):
    try:
        IDENTIFIER.validate_python(value, strict=True)
    except ValidationError as error:
        raise RepresentationError("representation_identifier") from error


def digest(value):
    try:
        DIGEST.validate_python(value, strict=True)
    except ValidationError as error:
        raise RepresentationError("representation_digest") from error


def record(value, model):
    require(model in (SchemaRef, Scope) and type(value) is model, "representation_reference_type")
    try:
        model.model_validate(value.model_dump(), strict=True)
    except ValidationError as error:
        raise RepresentationError("representation_reference_shape") from error


def text(value, maximum=1024, *, empty=False):
    require(type(value) is str and (0 if empty else 1) <= len(value) <= maximum, "representation_text_bound")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise RepresentationError("representation_text_utf8") from error


def labels(values):
    require(type(values) is tuple and 1 <= len(values) <= 16, "representation_label_bound")
    for value in values:
        text(value, 256)
    require(len(set(values)) == len(values), "representation_duplicate_label")


def fingerprint(value):
    body = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    require(len(body) <= 65536, "representation_descriptor_bound")
    return hashlib.sha256(body).hexdigest()
