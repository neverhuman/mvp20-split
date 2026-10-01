"""Preparation results own trace construction; artifacts must be finalized separately."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, SchemaRef
from amphora_contracts_evidence import (
    ConversionTrace,
    ConversionWarning,
    FieldOrigin,
    SourceSpan,
    TransformStep,
)

from .provenance import MAX_PROVENANCE_BYTES, ProvenanceError, SourceDocument, TraceDocument


def source_span(source: SourceDocument, start: int, end: int) -> SourceSpan:
    return SourceSpan(source=source.reference, unit="byte", start=start, end=end,
                      sha256=hashlib.sha256(source.content[start:end]).hexdigest())


@dataclass(frozen=True)
class PreparedAcquisition:
    source: SourceDocument
    converter_id: str
    content: bytes
    fields: tuple[FieldOrigin, ...]
    warnings: tuple[ConversionWarning, ...]
    disposition: str
    output_schema: SchemaRef

    def __post_init__(self):
        if len(self.content) > MAX_PROVENANCE_BYTES:
            raise ProvenanceError("prepared_output_limit")

    def trace(self, trace_id: str, finalized_output: ArtifactRef) -> TraceDocument:
        if finalized_output.schema_ref != self.output_schema or finalized_output.media_type != "application/json":
            raise ProvenanceError("prepared_schema_mismatch")
        # Fixed reviewed v1 profiles have no caller-supplied transformation configuration.
        config = hashlib.sha256(b"{}").hexdigest()
        record = ConversionTrace(
            wire_version="1", scope=self.source.reference.scope, trace_id=trace_id, source=self.source.reference,
            source_schema=self.source.reference.raw.schema_ref, target_schema=finalized_output.schema_ref,
            converter_id=self.converter_id, converter_version="1", configuration_sha256=config,
            transforms=(TransformStep(transform_id=self.converter_id, version="1",
                                      configuration_sha256=config, kind="deterministic"),),
            output=finalized_output, fields=self.fields, warnings=self.warnings, disposition=self.disposition,
        )
        return TraceDocument.verify(record, self.source, self.content)
