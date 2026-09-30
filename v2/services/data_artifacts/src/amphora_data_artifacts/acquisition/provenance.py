"""Exact-byte provenance verification independent of storage and scientific policy."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, Scope
from amphora_contracts_evidence import ConversionTrace, ConversionTraceRef, SourceRevisionRef, SourceSpan

MAX_PROVENANCE_BYTES = 4 * 1024 * 1024


class ProvenanceError(ValueError):
    """Stable safe code; never interpolate source content into diagnostics."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ProvenanceError(code)


def _verify_content(reference: ArtifactRef, scope: Scope, content: bytes) -> None:
    _require(reference.scope == scope, "artifact_scope_mismatch")
    _require(type(content) is bytes, "content_requires_bytes")
    _require(len(content) <= MAX_PROVENANCE_BYTES, "content_limit")
    _require(len(content) == reference.size_bytes, "content_size_mismatch")
    _require(hashlib.sha256(content).hexdigest() == reference.sha256, "content_digest_mismatch")


@dataclass(frozen=True)
class SourceDocument:
    """Caller obtains authorized bytes; this object verifies their attribution."""

    reference: SourceRevisionRef
    content: bytes

    def __post_init__(self) -> None:
        _verify_content(self.reference.raw, self.reference.scope, self.content)

    def extract(self, span: SourceSpan) -> bytes:
        _require(span.source == self.reference, "span_source_mismatch")
        _require(0 <= span.start <= span.end <= len(self.content), "span_bounds")
        result = self.content[span.start:span.end]
        _require(hashlib.sha256(result).hexdigest() == span.sha256, "span_digest_mismatch")
        return result


@dataclass(frozen=True, init=False)
class TraceDocument:
    """Verified cross-record invariants; creation requires exact source/output bytes.

    This is not an access grant, stored receipt or scientific acceptance. The
    acquisition store must separately enforce trace-id/content immutability.
    """

    trace: ConversionTrace
    canonical_bytes: bytes

    @classmethod
    def verify(cls, trace: ConversionTrace, source: SourceDocument, output: bytes) -> "TraceDocument":
        _require(trace.scope == source.reference.scope, "trace_scope_mismatch")
        _require(trace.source == source.reference, "trace_source_mismatch")
        _require(trace.source_schema == source.reference.raw.schema_ref, "source_schema_mismatch")
        _require(trace.target_schema == trace.output.schema_ref, "target_schema_mismatch")
        _verify_content(trace.output, trace.scope, output)
        paths: set[str] = set()
        has_unresolved = False
        for field in trace.fields:
            _require(field.target_path not in paths, "duplicate_field_path")
            paths.add(field.target_path)
            _require(len(set(field.step_indices)) == len(field.step_indices), "duplicate_step_reference")
            _require(all(index < len(trace.transforms) for index in field.step_indices), "unknown_step")
            kinds = {trace.transforms[index].kind for index in field.step_indices}
            for span in field.spans:
                source.extract(span)
            if field.origin in {"copied", "converted"}:
                _require(bool(field.spans), "missing_source_span")
                _require(bool(kinds) and kinds == {"deterministic"}, "origin_step_mismatch")
            elif field.origin == "inferred":
                _require("inference" in kinds, "origin_step_mismatch")
                has_unresolved = True
            else:
                has_unresolved = True
        _require(not (has_unresolved and trace.disposition == "normalized"), "unresolved_field_disposition")
        canonical = json.dumps(
            trace.model_dump(mode="json"), ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
        result = object.__new__(cls)
        object.__setattr__(result, "trace", trace)
        object.__setattr__(result, "canonical_bytes", canonical)
        return result

    def reference(self) -> ConversionTraceRef:
        return ConversionTraceRef(
            scope=self.trace.scope, trace_id=self.trace.trace_id,
            sha256=hashlib.sha256(self.canonical_bytes).hexdigest(),
        )
