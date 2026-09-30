"""Question priority and predeclared needs belong to Research, not Knowledge."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SafePositiveInt, SchemaRef, Scope, WireModel
from pydantic import Field

Description = Annotated[str, Field(min_length=1, max_length=2048)]


class ResearchQuestionRef(WireModel):
    scope: Scope
    question_id: Identifier
    revision: SafePositiveInt


class EvidenceNeedRef(WireModel):
    scope: Scope
    need_id: Identifier
    revision: SafePositiveInt


class AnswerCriterion(WireModel):
    criterion_id: Identifier
    description: Description


class ResearchQuestion(WireModel):
    wire_version: Literal["1"]
    reference: ResearchQuestionRef
    objective: Description
    applicability: ArtifactRef
    criteria: Annotated[tuple[AnswerCriterion, ...], Field(min_length=1, max_length=32)]
    supersedes: ResearchQuestionRef | None


class EvidenceNeed(WireModel):
    wire_version: Literal["1"]
    reference: EvidenceNeedRef
    question: ResearchQuestionRef
    criterion_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=32)]
    method: SchemaRef
    required_context: ArtifactRef
    supersedes: EvidenceNeedRef | None
