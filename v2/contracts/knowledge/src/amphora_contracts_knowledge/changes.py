"""Proposal and structural acceptance are distinct, attributable wire identities."""

from typing import Annotated, Literal

from amphora_contracts_core import (
    ArtifactRef,
    Digest,
    Finding,
    Identifier,
    SafePositiveInt,
    WireModel,
)
from amphora_contracts_evidence import ConversionTraceRef, SourceRevisionRef
from amphora_contracts_research import EvidenceNeedRef, ResearchQuestionRef
from pydantic import AwareDatetime, Field

from .operations import GraphOperation
from .records import ClaimGrounding, Description
from .references import (
    AcceptedChangeRef,
    DomainGraphRef,
    DomainHead,
    DomainRevisionRef,
    StructuralPolicyRef,
    VocabularyRef,
)


class GraphChangeProposal(WireModel):
    wire_version: Literal["1"]
    graph: DomainGraphRef
    change_id: Identifier
    base: DomainHead | None
    vocabulary: VocabularyRef
    policy: StructuralPolicyRef
    description: Description
    rationale: Description
    grounding: ClaimGrounding
    operations: Annotated[tuple[GraphOperation, ...], Field(min_length=1, max_length=128)]


class ReferenceValidation(WireModel):
    checked_at: AwareDatetime
    artifacts: Annotated[tuple[ArtifactRef, ...], Field(max_length=128)]
    sources: Annotated[tuple[SourceRevisionRef, ...], Field(max_length=128)]
    conversion_traces: Annotated[tuple[ConversionTraceRef, ...], Field(max_length=128)]
    questions: Annotated[tuple[ResearchQuestionRef, ...], Field(max_length=128)]
    evidence_needs: Annotated[tuple[EvidenceNeedRef, ...], Field(max_length=128)]


class AcceptedChangeContent(WireModel):
    proposal: GraphChangeProposal
    actor_id: Identifier
    policy: StructuralPolicyRef
    validation: ReferenceValidation
    accepted_at: AwareDatetime
    position: SafePositiveInt
    resulting_snapshot: DomainRevisionRef
    authority: Literal["structural_only"]


class AcceptedGraphChange(WireModel):
    wire_version: Literal["1"]
    reference: AcceptedChangeRef
    content: AcceptedChangeContent


class AcceptedDecision(WireModel):
    outcome: Literal["accepted"]
    head: DomainHead


class FailedDecision(WireModel):
    outcome: Literal["rejected", "conflict"]
    findings: Annotated[tuple[Finding, ...], Field(min_length=1, max_length=64)]


class GraphChangeDecision(WireModel):
    wire_version: Literal["1"]
    graph: DomainGraphRef
    change_id: Identifier
    request_sha256: Digest
    decision: Annotated[AcceptedDecision | FailedDecision, Field(discriminator="outcome")]


class GraphProposalStatus(WireModel):
    wire_version: Literal["1"]
    proposal: GraphChangeProposal
    actor_id: Identifier
    request_sha256: Digest
    registered_at: AwareDatetime
    decision: GraphChangeDecision | None
