"""Synthetic route/project assessment documents; no route-discovery or execution authority."""
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SchemaRef, WireModel
from pydantic import Field

from .identity import CandidateRevisionRef
from .measurements import MeasurementQuantity

RoutePosture = Literal["unassessed","proposed","precedent_supported","documented_target","demonstrated","no_route_found"]
StepPosture = Literal["unassessed","proposed","precedent_supported","documented_target","demonstrated"]
RouteRequiredPosture = Literal["proposed","precedent_supported","documented_target","demonstrated"]


class SynthesisContextRecord(WireModel):
    candidate: CandidateRevisionRef
    domain: Identifier
    purpose: Identifier
    conditions: ArtifactRef
    scale: MeasurementQuantity | None
    purity: ArtifactRef | None


class RouteProvenanceRecord(WireModel):
    method: SchemaRef
    tool: SchemaRef
    models: Annotated[tuple[SchemaRef, ...],Field(max_length=32)]
    sources: Annotated[tuple[ArtifactRef, ...],Field(max_length=128)]


class RouteStepRecord(WireModel):
    step_id: Identifier
    requires: Annotated[tuple[Identifier, ...],Field(max_length=64)]
    posture: StepPosture
    record: ArtifactRef
    sources: Annotated[tuple[ArtifactRef, ...],Field(max_length=64)]
    gaps: Annotated[tuple[Identifier, ...],Field(max_length=64)]


class RouteSearchRecord(WireModel):
    scope: ArtifactRef
    budget: MeasurementQuantity


class RouteEvidenceRecord(WireModel):
    context: SynthesisContextRecord
    route: ArtifactRef | None
    posture: RoutePosture
    provenance: RouteProvenanceRecord
    steps: Annotated[tuple[RouteStepRecord, ...],Field(max_length=256)]
    search: RouteSearchRecord | None
    next_checks: Annotated[tuple[Identifier, ...],Field(max_length=64)]


class RouteExecutionCheck(WireModel):
    criterion_id: Identifier
    disposition: Literal["met","failed","unknown"]
    evidence: Annotated[tuple[ArtifactRef, ...],Field(max_length=64)]
    reasons: Annotated[tuple[Identifier, ...],Field(min_length=1,max_length=64)]


class RouteOptionRecord(WireModel):
    evidence: RouteEvidenceRecord
    checks: Annotated[tuple[RouteExecutionCheck, ...],Field(max_length=128)]


class SynthesisProfile(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic"]
    reference: SchemaRef
    context: SynthesisContextRecord
    allowed_postures: Annotated[tuple[RouteRequiredPosture, ...],Field(min_length=1,max_length=4)]
    allowed_step_postures: Annotated[tuple[StepPosture, ...],Field(min_length=1,max_length=5)]
    required_checks: Annotated[tuple[Identifier, ...],Field(min_length=1,max_length=128)]


class RouteDecisionRecord(WireModel):
    option: RouteOptionRecord
    disposition: Literal["eligible","blocked","unknown"]
    blockers: Annotated[tuple[Identifier, ...],Field(max_length=128)]
    gaps: Annotated[tuple[Annotated[str,Field(min_length=1,max_length=160)], ...],Field(max_length=385)]


class SynthesisAssessment(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic"]
    policy: SynthesisProfile
    alternatives: Annotated[tuple[RouteDecisionRecord, ...],Field(min_length=1,max_length=64)]
