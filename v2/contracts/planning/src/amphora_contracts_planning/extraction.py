"""Attributed extraction candidates, never accepted graph or Research state."""

import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, Scope, WireModel
from amphora_contracts_evidence import ConversionTraceRef, SourceRevisionRef, SourceSpan
from amphora_contracts_knowledge import (
    DomainGraphRef,
    DomainHead,
    EntityRevisionRef,
    StructuralPolicyRef,
    VocabularyRef,
)
from amphora_contracts_research import AnswerCriterion, EvidenceNeedRef, ResearchQuestionRef
from pydantic import Field

from .engagement import EngagementRef

Text = Annotated[str, Field(min_length=1, max_length=4096)]


class ExtractionSource(WireModel):
    source: SourceRevisionRef
    conversion_traces: Annotated[tuple[ConversionTraceRef, ...], Field(min_length=1, max_length=8)]
    input_profile: Literal["raw_utf8_v1"]


class ExtractionTarget(WireModel):
    graph: DomainGraphRef
    base: DomainHead | None
    vocabulary: VocabularyRef
    policy: StructuralPolicyRef
    operation_schema: SchemaRef
    applicability: ArtifactRef | None


class ExtractionTask(WireModel):
    schema_version: Literal["1"] = "1"
    task_id: Identifier
    scope: Scope
    engagement: EngagementRef
    request_sha256: Digest
    sources: Annotated[tuple[ExtractionSource, ...], Field(min_length=1, max_length=16)]
    target: ExtractionTarget
    existing_entities: Annotated[tuple[EntityRevisionRef, ...], Field(max_length=128)]
    known_questions: Annotated[tuple[ResearchQuestionRef, ...], Field(max_length=64)]
    known_needs: Annotated[tuple[EvidenceNeedRef, ...], Field(max_length=64)]


class SourceQuotation(WireModel):
    span: SourceSpan
    text: Text


class ExtractionAttribution(WireModel):
    origin: Literal["source_stated", "inferred"]
    quotations: Annotated[tuple[SourceQuotation, ...], Field(min_length=1, max_length=16)]
    confidence: Literal["unknown", "low", "medium", "high"]


class ExtractionEntity(WireModel):
    local_id: Identifier
    label: Annotated[str, Field(min_length=1, max_length=512)]
    entity_type: Identifier
    matches: Annotated[tuple[EntityRevisionRef, ...], Field(max_length=8)]
    attribution: ExtractionAttribution


class ExtractionAssertion(WireModel):
    local_id: Identifier
    subject: Identifier
    predicate: Identifier
    object: Identifier
    statement: Text
    polarity: Literal["affirmed", "negated"]
    posture: Literal["reported", "hypothesis", "unresolved"]
    applicability: ArtifactRef | None
    attribution: ExtractionAttribution


class QuestionDraft(WireModel):
    local_id: Identifier
    objective: Annotated[str, Field(min_length=1, max_length=2048)]
    applicability: ArtifactRef | None
    criteria: Annotated[tuple[AnswerCriterion, ...], Field(min_length=1, max_length=32)]
    attribution: ExtractionAttribution


class AnswerDraft(WireModel):
    local_id: Identifier
    question_local_id: Identifier | None
    question: ResearchQuestionRef | None
    answer: Text
    validation_method: SchemaRef | None
    context: ArtifactRef | None
    attribution: ExtractionAttribution


class EvidenceNeedDraft(WireModel):
    local_id: Identifier
    question_local_id: Identifier | None
    question: ResearchQuestionRef | None
    criterion_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=32)]
    method: SchemaRef | None
    required_context: ArtifactRef | None
    attribution: ExtractionAttribution


class ExtractionDiagnostic(WireModel):
    code: Identifier
    target_path: Annotated[str, Field(min_length=1, max_length=256, pattern=r"^/")]
    kind: Literal["missing", "ambiguous", "contradiction", "unsupported"]
    description: Text


class ExtractionDraft(WireModel):
    schema_version: Literal["1"] = "1"
    action: Literal["propose_knowledge_change", "request_evidence", "abstain"]
    rationale: Text
    entities: Annotated[tuple[ExtractionEntity, ...], Field(max_length=64)]
    assertions: Annotated[tuple[ExtractionAssertion, ...], Field(max_length=64)]
    questions: Annotated[tuple[QuestionDraft, ...], Field(max_length=32)]
    answers: Annotated[tuple[AnswerDraft, ...], Field(max_length=32)]
    evidence_needs: Annotated[tuple[EvidenceNeedDraft, ...], Field(max_length=32)]
    diagnostics: Annotated[tuple[ExtractionDiagnostic, ...], Field(max_length=64)]


def extraction_draft_schema() -> SchemaRef:
    schema = ExtractionDraft.model_json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "urn:amphora:planning.extraction-draft:1:validation"
    raw = (json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False) + "\n").encode("utf-8")
    return SchemaRef(schema_id="planning.extraction-draft", version="1", sha256=hashlib.sha256(raw).hexdigest())
