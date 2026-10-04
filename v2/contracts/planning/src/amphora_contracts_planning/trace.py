"""Interpretation provenance, without Data or Knowledge acceptance authority."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, Scope, WireModel
from amphora_contracts_evidence import SourceSpan, TransformStep
from pydantic import Field

from .context import ModelBinding
from .engagement import ProviderAttemptRef
from .extraction import ExtractionDiagnostic, ExtractionSource, ExtractionTarget


class ExtractionTraceRef(WireModel):
    scope: Scope
    trace_id: Identifier
    sha256: Digest


class InterpretationOrigin(WireModel):
    target_path: Annotated[str, Field(min_length=1, max_length=256, pattern=r"^/")]
    origin: Literal["model_claimed_source", "model_inferred", "missing"]
    confidence: Literal["unknown", "low", "medium", "high"]
    spans: Annotated[tuple[SourceSpan, ...], Field(max_length=16)]


class InterpretationOutcome(WireModel):
    observation_sha256: Digest
    capture_sha256: Digest
    captured_bytes: Annotated[int, Field(ge=0, le=65536)]
    capture_complete: bool
    status: Literal["proposed", "abstained", "invalid", "unavailable", "unknown", "policy_rejected"]
    reason_code: Identifier | None
    candidate_sha256: Digest | None


class ExtractionTrace(WireModel):
    schema_version: Literal["1"] = "1"
    authority: Literal["interpretation_only"] = "interpretation_only"
    validation: Literal["profile_only"] = "profile_only"
    scope: Scope
    trace_id: Identifier
    task_id: Identifier
    task_sha256: Digest
    attempt: ProviderAttemptRef
    sources: Annotated[tuple[ExtractionSource, ...], Field(min_length=1, max_length=16)]
    target: ExtractionTarget
    model: ModelBinding
    prompt: ArtifactRef
    policy: ArtifactRef
    transforms: Annotated[tuple[TransformStep, ...], Field(min_length=1, max_length=8)]
    outcome: InterpretationOutcome
    fields: Annotated[tuple[InterpretationOrigin, ...], Field(max_length=768)]
    diagnostics: Annotated[tuple[ExtractionDiagnostic, ...], Field(max_length=64)]
    prior: ExtractionTraceRef | None
    repair_depth: Annotated[int, Field(ge=0, le=16)]
