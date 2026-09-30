"""Bounded wire provenance; services own conversion and disposition policy."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, Scope, WireModel
from pydantic import Field

from .references import SourceRevisionRef, SourceSpan

FieldPath = Annotated[str, Field(min_length=1, max_length=256, pattern=r"^/")]


class TransformStep(WireModel):
    transform_id: Identifier
    version: Identifier
    configuration_sha256: Digest
    kind: Literal["deterministic", "inference"]


class FieldOrigin(WireModel):
    """Missing values have no fabricated value; outputs live in scoped artifacts."""

    target_path: FieldPath
    origin: Literal["copied", "converted", "inferred", "missing"]
    spans: Annotated[tuple[SourceSpan, ...], Field(max_length=32)]
    step_indices: Annotated[
        tuple[Annotated[int, Field(ge=0, le=31)], ...], Field(max_length=32)
    ]


class ConversionWarning(WireModel):
    code: Identifier
    target_path: FieldPath | None


class ConversionTrace(WireModel):
    wire_version: Literal["1"]
    scope: Scope
    trace_id: Identifier
    source: SourceRevisionRef
    source_schema: SchemaRef
    target_schema: SchemaRef
    converter_id: Identifier
    converter_version: Identifier
    configuration_sha256: Digest
    transforms: Annotated[tuple[TransformStep, ...], Field(min_length=1, max_length=32)]
    output: ArtifactRef
    fields: Annotated[tuple[FieldOrigin, ...], Field(min_length=1, max_length=256)]
    warnings: Annotated[tuple[ConversionWarning, ...], Field(max_length=64)]
    disposition: Literal["normalized", "unresolved", "quarantined"]
