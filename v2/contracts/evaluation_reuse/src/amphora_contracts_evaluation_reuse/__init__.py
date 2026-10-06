"""Synthetic owner reuse decisions preserve original producer and target context."""
from typing import Annotated, Literal

from amphora_contracts_candidate_canonicalization import CanonicalCandidate
from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, Scope, WireModel
from amphora_contracts_evaluation_identity import EvaluationIdentityInput, EvaluationReusePolicy
from amphora_contracts_execution_proofs import AcceptedToolExecution
from amphora_contracts_research import CandidateRevision, CandidateRevisionRef, EligibilityDecision, ScientificDecisionRef, SynthesisDecision
from amphora_contracts_synthetic_evaluation import SyntheticEvaluationReceipt
from amphora_contracts_tools import ToolBinding
from pydantic import Field


class ProducerRef(WireModel):
    scope: Scope
    run_id: Identifier
    completion_id: Identifier


class ReuseProfile(WireModel):
    wire_version: Literal['1']
    authority: Literal['synthetic']
    scope: Scope
    evaluation: EvaluationReusePolicy
    canonicalizer: ToolBinding
    synthesis_required: bool


class ReuseProfileRef(WireModel):
    scope: Scope
    policy: SchemaRef


class ReuseCandidateInput(WireModel):
    candidate: CandidateRevisionRef
    identity: ArtifactRef
    canonicalization: ProducerRef


class ReuseRequest(WireModel):
    wire_version: Literal['1']
    reuse_id: Identifier
    profile: ReuseProfileRef
    source: ReuseCandidateInput
    target: ReuseCandidateInput
    evaluation: ProducerRef
    eligibility: ScientificDecisionRef
    synthesis: ScientificDecisionRef


class ReuseSelection(WireModel):
    scope: Scope
    reuse_id: Identifier


class ReuseRef(ReuseSelection):
    sha256: Digest


class ReuseCandidateEvidence(WireModel):
    candidate: CandidateRevision
    declaration: EvaluationIdentityInput
    producer: AcceptedToolExecution
    canonicalization: CanonicalCandidate


class ReuseEvaluationEvidence(WireModel):
    producer: AcceptedToolExecution
    receipt: SyntheticEvaluationReceipt


class ReuseProjection(WireModel):
    wire_version: Literal['1']
    authority: Literal['synthetic_reuse_decision']
    reference: ReuseRef
    actor_id: Identifier
    profile: ReuseProfile
    request: ReuseRequest
    source: ReuseCandidateEvidence
    target: ReuseCandidateEvidence
    evaluation: ReuseEvaluationEvidence
    eligibility: EligibilityDecision
    synthesis: SynthesisDecision
    status: Literal['permitted','miss','ineligible']
    reusable_artifact: ArtifactRef | None
    reasons: Annotated[tuple[Identifier, ...], Field(max_length=16)]
    focus: Annotated[tuple[Annotated[str, Field(min_length=1, max_length=160)], ...], Field(max_length=256)]
    sources: Annotated[tuple[ArtifactRef, ...], Field(min_length=1, max_length=128)]
