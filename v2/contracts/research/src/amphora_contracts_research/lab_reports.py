"""Explicit synthetic producer payload and owner reconciliation; no evidence promotion."""
import hashlib
import json
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Identifier, SchemaRef, WireModel
from pydantic import Field

from .experiments import ExperimentRevisionRef
from .measurements import MeasurementValue
from .observations import (
    ObservationBindingRecord,
    ObservationQuality,
    ObservationRevision,
    ObservationRevisionRef,
)


class ReportedObservation(WireModel):
    reference: ObservationRevisionRef
    supersedes: ObservationRevisionRef | None
    binding: ObservationBindingRecord
    value: MeasurementValue
    quality: ObservationQuality


class SyntheticLabReport(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic"]
    issuer: Identifier
    adapter: SchemaRef
    raw_report: ArtifactRef
    observations: Annotated[tuple[ReportedObservation, ...],Field(max_length=64)]


class LabReturnProfile(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic"]
    profile_id: Identifier
    version: Identifier
    experiment: ExperimentRevisionRef
    adapter: SchemaRef
    publishers: Annotated[tuple[Identifier, ...],Field(min_length=1,max_length=32)]


class ObservationMatchRecord(WireModel):
    observation: ObservationRevisionRef
    disposition: Literal["matched","quarantined"]
    reasons: Annotated[tuple[Identifier, ...],Field(max_length=16)]
    state_known: bool


class LabReportResolution(WireModel):
    wire_version: Literal["1"]
    authority: Literal["synthetic"]
    source: ArtifactRef
    raw_report: ArtifactRef
    profile: LabReturnProfile
    disposition: Literal["complete","partial","unmatched"]
    observations: Annotated[tuple[ObservationRevision, ...],Field(max_length=64)]
    matches: Annotated[tuple[ObservationMatchRecord, ...],Field(max_length=64)]
    missing_expectations: Annotated[tuple[Identifier, ...],Field(max_length=1024)]
    unavailable_values: Annotated[tuple[ObservationRevisionRef, ...],Field(max_length=64)]


def synthetic_lab_report_schema_document():
    schema = SyntheticLabReport.model_json_schema(mode="serialization")
    return json.dumps(schema,sort_keys=True,separators=(",", ":"),ensure_ascii=False,allow_nan=False).encode("utf-8")


def synthetic_lab_report_schema():
    return SchemaRef(schema_id="research.synthetic-lab-report.payload",version="1",
                     sha256=hashlib.sha256(synthetic_lab_report_schema_document()).hexdigest())
