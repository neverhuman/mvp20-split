"""Reviewed compiler metadata for forms, distinct from live Registry eligibility."""

import base64
from typing import Annotated, Literal

from amphora_contracts_core import Digest, SchemaRef, Scope, WireModel
from amphora_contracts_tools import LockEntry
from pydantic import Field, field_validator


class DefinitionUniverse(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    universe_sha256: Digest
    authority: Literal["compiler_configuration"] = "compiler_configuration"
    reviewed_tools: Annotated[tuple[LockEntry, ...], Field(max_length=64)]
    schemas: Annotated[tuple[SchemaRef, ...], Field(max_length=256)]


class DefinitionSchema(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    universe_sha256: Digest
    reference: SchemaRef
    schema_bytes_base64: Annotated[str, Field(min_length=4, max_length=87384, pattern=r"^[A-Za-z0-9+/]+={0,2}$")]

    @field_validator("schema_bytes_base64")
    @classmethod
    def bounded_bytes(cls, value):
        raw = base64.b64decode(value, validate=True)
        if len(raw) > 65536 or base64.b64encode(raw).decode("ascii") != value:
            raise ValueError("invalid_schema_byte_envelope")
        return value
