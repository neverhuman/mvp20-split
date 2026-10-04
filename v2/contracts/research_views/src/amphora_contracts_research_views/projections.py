"""Scientific context is retained; shape validity conveys no scientific authority."""

import re
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, WireModel
from amphora_contracts_research import (
    CandidateRevisionRef,
    CategoricalMeasurement,
    CensoredMeasurement,
    ExperimentExpectation,
    ExperimentProtocol,
    MaterialStateRevisionRef,
    MissingMeasurement,
    NumericMeasurement,
    ObservationBindingRecord,
    ObservationQuality,
    ObservationRevisionRef,
    SampleIdentity,
    SeriesMeasurementPoint,
)
from pydantic import Field

from .queries import (
    ObservationSeriesRequest,
    PropertyViewRequest,
    ResearchViewPosition,
    SpecimenViewRequest,
)

Unit = Annotated[
    str, Field(min_length=1, max_length=32, pattern=re.compile(r"^\S+$(?![\s\S])"))
]


class MaterialStateSummary(WireModel):
    reference: MaterialStateRevisionRef
    candidate: CandidateRevisionRef
    supersedes: MaterialStateRevisionRef | None
    preparation_count: Annotated[int, Field(ge=0, le=256)]
    feature_count: Annotated[int, Field(ge=0, le=128)]


class SpecimenViewRow(WireModel):
    sample: SampleIdentity
    material: MaterialStateSummary | None


class SpecimenViewPage(WireModel):
    wire_version: Literal["1"]
    request: SpecimenViewRequest
    query_sha256: Digest
    total: Annotated[int, Field(ge=1, le=256)]
    rows: Annotated[tuple[SpecimenViewRow, ...], Field(max_length=16)]
    next_position: ResearchViewPosition | None


class SeriesDescriptor(WireModel):
    kind: Literal["series"]
    x_unit: Unit
    y_unit: Unit
    point_count: Annotated[int, Field(ge=1, le=4096)]


MeasurementPreview = Annotated[
    NumericMeasurement
    | CensoredMeasurement
    | CategoricalMeasurement
    | MissingMeasurement
    | SeriesDescriptor,
    Field(discriminator="kind"),
]


class PropertyViewRow(WireModel):
    reference: ObservationRevisionRef
    supersedes: ObservationRevisionRef | None
    source: ArtifactRef
    binding: ObservationBindingRecord
    quality: ObservationQuality
    value: MeasurementPreview
    context_link: Literal[
        "declared_expectation", "unbound", "different_experiment", "unknown_expectation"
    ]
    expectation: ExperimentExpectation | None


class PropertyViewPage(WireModel):
    wire_version: Literal["1"]
    request: PropertyViewRequest
    query_sha256: Digest
    total: Annotated[int, Field(ge=1, le=128)]
    protocol: ExperimentProtocol
    authority: Literal["reported_evidence_only"]
    selection_scope: Literal["explicit_observation_revisions"]
    rows: Annotated[tuple[PropertyViewRow, ...], Field(max_length=16)]
    next_position: ResearchViewPosition | None


class ObservationSeriesPage(WireModel):
    wire_version: Literal["1"]
    request: ObservationSeriesRequest
    query_sha256: Digest
    total: Annotated[int, Field(ge=1, le=4096)]
    x_unit: Unit
    y_unit: Unit
    source: ArtifactRef
    binding: ObservationBindingRecord
    quality: ObservationQuality
    points: Annotated[tuple[SeriesMeasurementPoint, ...], Field(max_length=256)]
    next_position: ResearchViewPosition | None
