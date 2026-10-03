"""Attributable preparation/features; schemas do not establish measured truth."""
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SchemaRef, WireModel
from pydantic import Field

from .identity import CandidateRevisionRef, MaterialStateRevisionRef
from .measurements import MeasurementQuantity, MeasurementValue


class ProcessingCondition(WireModel):
    name: Identifier
    quantity: MeasurementQuantity


class ProcessingContextRecord(WireModel):
    method: SchemaRef
    conditions: Annotated[tuple[ProcessingCondition, ...],Field(max_length=64)]
    duration: MeasurementQuantity | None
    atmosphere: Annotated[str,Field(min_length=1,max_length=128)] | None


class ProcessingAttribution(WireModel):
    basis: Literal["proposed","observed"]
    actor: Identifier
    equipment: Annotated[tuple[Identifier, ...],Field(max_length=32)] | None
    source: ArtifactRef


class ProcessingEventRecord(WireModel):
    event_id: Identifier
    context: ProcessingContextRecord
    attribution: ProcessingAttribution


class MaterialFeatureEvidence(WireModel):
    basis: Literal["measured","inferred","unknown"]
    method: SchemaRef | None
    source: ArtifactRef | None


class MaterialFeatureRecord(WireModel):
    name: Identifier
    value: MeasurementValue
    evidence: MaterialFeatureEvidence


class MaterialStateRevision(WireModel):
    wire_version: Literal["1"]
    reference: MaterialStateRevisionRef
    candidate: CandidateRevisionRef
    supersedes: MaterialStateRevisionRef | None
    preparation: Annotated[tuple[ProcessingEventRecord, ...],Field(max_length=256)]
    features: Annotated[tuple[MaterialFeatureRecord, ...],Field(max_length=128)]
