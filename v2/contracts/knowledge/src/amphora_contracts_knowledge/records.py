"""Knowledge transport records; cross-record semantics belong to the owner."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SchemaRef, WireModel
from amphora_contracts_evidence import ConversionTraceRef, SourceSpan
from amphora_contracts_research import EvidenceNeedRef, ResearchQuestionRef
from pydantic import Field

from .references import AssertionRevisionRef, EntityRevisionRef

Description = Annotated[str, Field(min_length=1, max_length=4096)]


class PredicateDefinition(WireModel):
    predicate_id: Identifier
    description: Description
    subject_types: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=64)]
    object_types: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=64)]


class DomainVocabulary(WireModel):
    wire_version: Literal["1"]
    vocabulary_id: Identifier
    version: Identifier
    entity_types: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=64)]
    predicates: Annotated[tuple[PredicateDefinition, ...], Field(min_length=1, max_length=128)]


class ClaimGrounding(WireModel):
    spans: Annotated[tuple[SourceSpan, ...], Field(min_length=1, max_length=64)]
    conversion_traces: Annotated[tuple[ConversionTraceRef, ...], Field(min_length=1, max_length=64)]
    interpretation_artifacts: Annotated[tuple[ArtifactRef, ...], Field(max_length=16)]


class QuestionEvidenceLink(WireModel):
    question: ResearchQuestionRef
    need: EvidenceNeedRef | None
    role: Literal["proposed_answer", "support", "contradiction", "context"]
    answer_proposal: ArtifactRef | None
    validation_method: SchemaRef | None


class DomainEntity(WireModel):
    reference: EntityRevisionRef
    entity_type: Identifier
    label: Annotated[str, Field(min_length=1, max_length=512)]
    context: ArtifactRef
    supersedes: EntityRevisionRef | None


class DomainAssertion(WireModel):
    reference: AssertionRevisionRef
    subject: EntityRevisionRef
    predicate: Identifier
    object: EntityRevisionRef
    statement: Description
    polarity: Literal["affirmed", "negated"]
    posture: Literal["reported", "hypothesis", "unresolved"]
    applicability: ArtifactRef
    grounding: ClaimGrounding
    research_links: Annotated[tuple[QuestionEvidenceLink, ...], Field(max_length=32)]
    supersedes: AssertionRevisionRef | None


class EntityAlias(WireModel):
    source: EntityRevisionRef
    target: EntityRevisionRef
    change_id: Identifier


class AssertionRetraction(WireModel):
    assertion: AssertionRevisionRef
    change_id: Identifier
