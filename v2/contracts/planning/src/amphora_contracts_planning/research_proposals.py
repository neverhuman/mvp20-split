"""Attributed proposals for owner handoff, never accepted Research evidence."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Finding, Identifier, SchemaRef, WireModel
from amphora_contracts_knowledge import ClaimGrounding
from amphora_contracts_research import EvidenceNeed, ResearchQuestion, ResearchQuestionRef
from pydantic import Field

from .extraction import ExtractionAttribution, Text

CandidatePath = Annotated[str, Field(min_length=1, max_length=256, pattern=r'^/')]


class _AttributedProposal(WireModel):
    local_id: Identifier
    source_path: CandidatePath
    model_attribution: ExtractionAttribution
    grounding: ClaimGrounding


class QuestionProposal(_AttributedProposal):
    question: ResearchQuestion


class AnswerProposal(_AttributedProposal):
    question: ResearchQuestionRef
    answer: Text
    validation_method: SchemaRef
    context: ArtifactRef


class NeedProposal(_AttributedProposal):
    need: EvidenceNeed


class ResearchProposalSet(WireModel):
    wire_version: Literal['1']
    authority: Literal['proposal_only']
    validation: Literal['quotation_and_structure_only']
    task_sha256: Digest
    candidate_sha256: Digest
    interpretation: ArtifactRef
    outcome: Literal['proposed', 'partial', 'unresolved', 'abstained']
    questions: Annotated[tuple[QuestionProposal, ...], Field(max_length=32)]
    answers: Annotated[tuple[AnswerProposal, ...], Field(max_length=32)]
    evidence_needs: Annotated[tuple[NeedProposal, ...], Field(max_length=32)]
    findings: Annotated[tuple[Finding, ...], Field(max_length=256)]
    withheld: Annotated[tuple[CandidatePath, ...], Field(max_length=96)]
