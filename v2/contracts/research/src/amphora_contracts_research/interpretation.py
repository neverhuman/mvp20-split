"""Policy interpretations retain original evidence; they grant no execution or truth authority."""
from typing import Annotated, Literal

from amphora_contracts_core import ArtifactRef, Digest, Identifier, SchemaRef, Scope, WireModel
from pydantic import Field

from .experiments import ExperimentDefinition, ExperimentRevisionRef
from .measurements import DecimalText, MeasurementValue, UnitToken
from .observations import ObservationRevision, ObservationRevisionRef


class ConversionRuleRecord(WireModel):
    dimension: Identifier
    source_unit: UnitToken
    target_unit: UnitToken
    scale: DecimalText


class ConversionCatalogRecord(WireModel):
    profile_id: Identifier
    version: Identifier
    reference: SchemaRef
    rules: Annotated[tuple[ConversionRuleRecord, ...],Field(min_length=1,max_length=128)]


class ObservationUseRequirements(WireModel):
    available_value: bool
    passed_controls: bool
    bound_state: bool
    excluded_flags: Annotated[tuple[Identifier, ...],Field(max_length=64)]


class ObservationUsePolicyRecord(WireModel):
    profile_id: Identifier
    version: Identifier
    reference: SchemaRef
    action: Identifier
    requirements: ObservationUseRequirements
    normalization: ConversionCatalogRecord | None


class InterpretationProfileRef(WireModel):
    scope: Scope
    kind: Literal["normalization","observation-use"]
    policy: SchemaRef


class NormalizationProfile(WireModel):
    wire_version: Literal["1"]
    kind: Literal["normalization"]
    scope: Scope
    catalog: ConversionCatalogRecord


class ObservationUseProfile(WireModel):
    wire_version: Literal["1"]
    kind: Literal["observation-use"]
    scope: Scope
    policy: ObservationUsePolicyRecord


class NormalizationTargetRecord(WireModel):
    value_unit: UnitToken
    coordinate_unit: UnitToken | None


class NormalizeObservationRequest(WireModel):
    wire_version: Literal["1"]
    kind: Literal["normalization"]
    interpretation_id: Identifier
    profile: InterpretationProfileRef
    observation: ObservationRevisionRef
    targets: NormalizationTargetRecord


class AssessObservationUseRequest(WireModel):
    wire_version: Literal["1"]
    kind: Literal["observation-use"]
    interpretation_id: Identifier
    profile: InterpretationProfileRef
    experiment: ExperimentRevisionRef
    observations: Annotated[tuple[ObservationRevisionRef, ...],Field(max_length=1024)]


class NormalizedMeasurementRecord(WireModel):
    original: MeasurementValue
    targets: NormalizationTargetRecord
    policy: SchemaRef
    status: Literal["normalized","unresolved"]
    normalized: MeasurementValue | None
    applied: Annotated[tuple[ConversionRuleRecord, ...],Field(max_length=2)]
    reason: Identifier | None


class InterpretationMatchRecord(WireModel):
    disposition: Literal["matched","quarantined"]
    reasons: Annotated[tuple[Identifier, ...],Field(max_length=32)]
    state_bound: bool


class ObservationUseReviewRecord(WireModel):
    observation: ObservationRevision
    raw_match: InterpretationMatchRecord
    effective_match: InterpretationMatchRecord
    normalization: NormalizedMeasurementRecord | None
    disposition: Literal["usable","excluded","unresolved","quarantined"]
    blockers: Annotated[tuple[Identifier, ...],Field(max_length=64)]
    gaps: Annotated[tuple[Identifier, ...],Field(max_length=64)]
    focus: Annotated[tuple[Identifier, ...],Field(max_length=64)]


class InterpretationRef(WireModel):
    scope: Scope
    kind: Literal["normalization","observation-use"]
    interpretation_id: Identifier
    sha256: Digest


class NormalizationProjection(WireModel):
    wire_version: Literal["1"]
    authority: Literal["policy_interpretation"]
    kind: Literal["normalization"]
    reference: InterpretationRef
    actor_id: Identifier
    profile: NormalizationProfile
    observation: ObservationRevision
    result: NormalizedMeasurementRecord
    sources: Annotated[tuple[ArtifactRef, ...],Field(max_length=128)]


class ObservationUseProjection(WireModel):
    wire_version: Literal["1"]
    authority: Literal["policy_interpretation"]
    kind: Literal["observation-use"]
    reference: InterpretationRef
    actor_id: Identifier
    profile: ObservationUseProfile
    experiment: ExperimentDefinition
    reviews: Annotated[tuple[ObservationUseReviewRecord, ...],Field(max_length=1024)]
    usable: Annotated[tuple[ObservationRevisionRef, ...],Field(max_length=1024)]
    focus: Annotated[tuple[ObservationRevisionRef, ...],Field(max_length=1024)]
    missing_expectations: Annotated[tuple[Identifier, ...],Field(max_length=1024)]
    sources: Annotated[tuple[ArtifactRef, ...],Field(max_length=128)]
