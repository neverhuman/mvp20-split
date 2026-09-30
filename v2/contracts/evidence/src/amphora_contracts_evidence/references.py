"""Immutable acquisition references; validation grants no owner authority."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, SafePositiveInt, Scope, WireModel
from pydantic import Field

SafeOffset = Annotated[int, Field(ge=0, le=9007199254740991)]


class SourceRevisionRef(WireModel):
    scope: Scope
    source_id: Identifier
    revision_id: Identifier
    raw: ArtifactRef


class SourceSpan(WireModel):
    """Half-open byte range; owner verifies ordering, bounds and exact content."""

    source: SourceRevisionRef
    unit: Literal["byte"]
    start: SafeOffset
    end: SafeOffset
    sha256: Digest


class RightsRevisionRef(WireModel):
    scope: Scope
    rights_id: Identifier
    revision: SafePositiveInt


class ConversionTraceRef(WireModel):
    scope: Scope
    trace_id: Identifier
    sha256: Digest
