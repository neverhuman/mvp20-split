"""Bounded logical entailment contracts; scientific authority is deliberately absent."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, WireModel
from pydantic import Field

from .changes import ReferenceValidation
from .references import AssertionRevisionRef, DomainGraphRef, DomainRevisionRef, EntityRevisionRef


class GroundLiteral(WireModel):
    subject: EntityRevisionRef
    predicate: Identifier
    object: EntityRevisionRef
    polarity: Literal["affirmed", "negated"]


class GroundRule(WireModel):
    rule_id: Identifier
    premises: Annotated[tuple[GroundLiteral, ...], Field(min_length=1, max_length=16)]
    conclusion: GroundLiteral


class ReasoningLimits(WireModel):
    depth: Annotated[int, Field(ge=1, le=64)]
    work: Annotated[int, Field(ge=1, le=1_000_000)]
    facts: Annotated[int, Field(ge=1, le=8192)]


class RuleSetRef(WireModel):
    graph: DomainGraphRef
    rule_set_id: Identifier
    version: Identifier
    sha256: Digest


class ReasoningRuleSet(WireModel):
    wire_version: Literal["1"]
    graph: DomainGraphRef
    rule_set_id: Identifier
    version: Identifier
    authority: Literal["synthetic_logical_entailment"]
    context: ArtifactRef
    limits: ReasoningLimits
    rules: Annotated[tuple[GroundRule, ...], Field(max_length=256)]


class ReasoningRequest(WireModel):
    wire_version: Literal["1"]
    request_id: Identifier
    snapshot: DomainRevisionRef
    rule_set: RuleSetRef
    context: ArtifactRef
    subject: ArtifactRef
    purpose: Identifier
    targets: Annotated[tuple[GroundLiteral, ...], Field(min_length=1, max_length=128)]


class ReasoningFinding(WireModel):
    target: GroundLiteral
    status: Literal["supported", "contradicted", "unknown"]
    positive: bool
    negative: bool
    conflict: bool
    supporting_assertions: Annotated[tuple[AssertionRevisionRef, ...], Field(max_length=8192)]
    opposing_assertions: Annotated[tuple[AssertionRevisionRef, ...], Field(max_length=8192)]


class DerivationStep(WireModel):
    fact: GroundLiteral
    depth: Annotated[int, Field(ge=0, le=64)]
    rule_id: Identifier | None
    premises: Annotated[tuple[GroundLiteral, ...], Field(max_length=16)]
    assertions: Annotated[tuple[AssertionRevisionRef, ...], Field(max_length=8192)]


class CompleteReasoning(WireModel):
    status: Literal["complete"]


class IncompleteReasoning(WireModel):
    status: Literal["incomplete"]
    code: Literal["reasoning_work_limit", "reasoning_depth_limit", "reasoning_fact_limit"]


class ReasoningResult(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic_logical_entailment"]
    request: ReasoningRequest
    outcome: Annotated[CompleteReasoning | IncompleteReasoning, Field(discriminator="status")]
    work: Annotated[int, Field(ge=0, le=1_000_000)]
    findings: Annotated[tuple[ReasoningFinding, ...], Field(min_length=1, max_length=128)]
    steps: Annotated[tuple[DerivationStep, ...], Field(max_length=8192)]
    excluded_context: Annotated[tuple[AssertionRevisionRef, ...], Field(max_length=8192)]


class EvaluatedReasoning(WireModel):
    outcome: Literal["evaluated"]
    result: ReasoningResult
    validation: ReferenceValidation


class FailedReasoning(WireModel):
    outcome: Literal["failed"]
    code: Identifier


class ReasoningStatus(WireModel):
    wire_version: Literal["1"]
    request: ReasoningRequest
    actor_id: Identifier
    decision: Annotated[EvaluatedReasoning | FailedReasoning, Field(discriminator="outcome")] | None
