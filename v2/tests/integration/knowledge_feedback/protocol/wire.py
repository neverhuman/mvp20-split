"""Verification-only manifest DTOs using existing public owner references."""

from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SchemaRef, Scope, WireModel
from amphora_contracts_evidence import ConversionTraceRef, SourceSpan
from amphora_contracts_graph_runtime import GraphReadCut
from amphora_contracts_knowledge import AssertionRevisionRef, DomainRevisionRef
from amphora_contracts_representations import EncodingProfileRef, IndexGenerationRef
from amphora_contracts_research import (
    CandidateRevisionRef,
    EvidenceNeedRef,
    ExperimentRevisionRef,
    MaterialStateRevisionRef,
    ObservationRevisionRef,
    ResearchQuestionRef,
    SampleRevisionRef,
)
from pydantic import Field


class QuestionPins(WireModel):
    question: ResearchQuestionRef
    need: EvidenceNeedRef
    method: SchemaRef


class SourcePins(WireModel):
    span: SourceSpan
    trace: ConversionTraceRef


class GraphPins(WireModel):
    snapshot: DomainRevisionRef
    assertion: AssertionRevisionRef


class SpecimenPins(WireModel):
    key: Identifier
    candidate: CandidateRevisionRef
    material: MaterialStateRevisionRef
    sample: SampleRevisionRef
    experiment: ExperimentRevisionRef
    observation: ObservationRevisionRef


class RepresentationPins(WireModel):
    profile: EncodingProfileRef
    generation: IndexGenerationRef


class CampaignPins(WireModel):
    cut: GraphReadCut
    receipt: ArtifactRef


class ViewPin(WireModel):
    owner: Literal["knowledge", "research", "data", "campaign-runtime"]
    view_id: Identifier
    version: Identifier
    result_schema: SchemaRef


class FixtureManifest(WireModel):
    format: Literal["amphora.knowledge-feedback-fixture.v1"]
    authority: Literal["declared_fixture_only"]
    scenario_id: Identifier
    scope: Scope
    question: QuestionPins
    source: SourcePins
    graph: GraphPins
    specimens: Annotated[tuple[SpecimenPins, ...], Field(min_length=1, max_length=16)]
    representation: RepresentationPins
    campaign: CampaignPins
    views: Annotated[tuple[ViewPin, ...], Field(min_length=1, max_length=16)]
