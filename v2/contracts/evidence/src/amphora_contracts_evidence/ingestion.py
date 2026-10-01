"""Staged ingestion transport; prepared bytes are not finalized artifacts."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, WireModel
from pydantic import Field

from .conversion import ConversionWarning
from .references import SourceRevisionRef
from .sources import SourceRevision


class PreparedSource(WireModel):
    wire_version: Literal["1"]
    source: SourceRevisionRef
    content_json_utf8: Annotated[str, Field(max_length=4194304)]
    sha256: Digest
    schema_ref: SchemaRef
    disposition: Literal["normalized", "unresolved", "quarantined"]
    warnings: Annotated[tuple[ConversionWarning, ...], Field(max_length=64)]


class RetainPreparedSource(WireModel):
    wire_version: Literal["1"]
    source: SourceRevision
    trace_id: Identifier
    output: ArtifactRef
