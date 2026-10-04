/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Authority = "reported_evidence_only";
export type Offset = number;
export type QuerySha256 = string;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2561 = string;
export type SizeBytes = number;
export type QuerySha2561 = string;
export type ExperimentId = string;
export type Revision = number;
export type Limit = number;
export type ObservationId = string;
export type Revision1 = number;
/**
 * @minItems 1
 * @maxItems 128
 */
export type Observations = ObservationRevisionRef[];
export type WireVersion = "1";
export type Role = ("sample" | "positive_control" | "negative_control" | "blank") | null;
export type MaterialStateId = string;
export type Revision2 = number;
export type Revision3 = number;
export type SampleId = string;
export type ExpectationId = string | null;
export type ReplicateId = string | null;
export type ContextLink = "declared_expectation" | "unbound" | "different_experiment" | "unknown_expectation";
export type ExpectationId1 = string;
export type CriterionId = string;
export type Kind = "numeric" | "categorical" | "series";
export type Unit = string | null;
export type XUnit = string | null;
export type ReplicateId1 = string;
export type Role1 = "sample" | "positive_control" | "negative_control" | "blank";
export type Controls = "passed" | "failed" | "unknown";
/**
 * @maxItems 64
 */
export type Flags = string[];
export type Value =
  NumericMeasurement | CensoredMeasurement | CategoricalMeasurement | MissingMeasurement | SeriesDescriptor;
export type Kind1 = "numeric";
export type Unit1 = string;
export type Value1 = string;
export type Description = string;
export type Kind2 = "censored";
export type Inclusive = boolean;
export type Kind3 = "categorical";
export type Label = string;
export type Kind4 = "missing";
export type Reason = string;
export type Kind5 = "series";
export type PointCount = number;
export type XUnit1 = string;
export type YUnit = string;
/**
 * @maxItems 16
 */
export type Rows = PropertyViewRow[];
export type SelectionScope = "explicit_observation_revisions";
export type Total = number;
export type WireVersion1 = "1";

export interface PropertyViewPage {
  authority: Authority;
  next_position: ResearchViewPosition | null;
  protocol: ExperimentProtocol;
  query_sha256: QuerySha2561;
  request: PropertyViewRequest;
  rows: Rows;
  selection_scope: SelectionScope;
  total: Total;
  wire_version: WireVersion1;
}
export interface ResearchViewPosition {
  offset: Offset;
  query_sha256: QuerySha256;
}
export interface ExperimentProtocol {
  applicability: ArtifactRef;
  method: SchemaRef;
  source: ArtifactRef;
}
export interface ArtifactRef {
  artifact_id: ArtifactId;
  media_type: MediaType;
  schema_ref: SchemaRef;
  scope: Scope;
  sha256: Sha2561;
  size_bytes: SizeBytes;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha256;
  version: Version;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface PropertyViewRequest {
  experiment: ExperimentRevisionRef;
  limit?: Limit;
  observations: Observations;
  position?: ResearchViewPosition | null;
  wire_version: WireVersion;
}
export interface ExperimentRevisionRef {
  experiment_id: ExperimentId;
  revision: Revision;
  scope: Scope;
}
export interface ObservationRevisionRef {
  observation_id: ObservationId;
  revision: Revision1;
  scope: Scope;
}
export interface PropertyViewRow {
  binding: ObservationBindingRecord;
  context_link: ContextLink;
  expectation: ExperimentExpectation | null;
  quality: ObservationQuality;
  reference: ObservationRevisionRef;
  source: ArtifactRef;
  supersedes: ObservationRevisionRef | null;
  value: Value;
}
export interface ObservationBindingRecord {
  measurement: ObservationMethod;
  role: Role;
  specimen: ObservationSpecimen;
  target: ObservationTarget;
}
export interface ObservationMethod {
  context: ArtifactRef | null;
  method: SchemaRef | null;
}
export interface ObservationSpecimen {
  material_state: MaterialStateRevisionRef | null;
  sample: SampleRevisionRef | null;
}
export interface MaterialStateRevisionRef {
  material_state_id: MaterialStateId;
  revision: Revision2;
  scope: Scope;
}
export interface SampleRevisionRef {
  revision: Revision3;
  sample_id: SampleId;
  scope: Scope;
}
export interface ObservationTarget {
  expectation_id: ExpectationId;
  experiment: ExperimentRevisionRef | null;
  replicate_id: ReplicateId;
}
export interface ExperimentExpectation {
  expectation_id: ExpectationId1;
  readout: ExperimentReadout;
  replicate: ExperimentReplicate;
  sample: SampleRevisionRef;
}
export interface ExperimentReadout {
  criterion_id: CriterionId;
  kind: Kind;
  unit: Unit;
  x_unit: XUnit;
}
export interface ExperimentReplicate {
  replicate_id: ReplicateId1;
  role: Role1;
}
export interface ObservationQuality {
  controls: Controls;
  flags: Flags;
}
export interface NumericMeasurement {
  kind: Kind1;
  quantity: MeasurementQuantity;
  uncertainty: MeasurementInterval | null;
}
export interface MeasurementQuantity {
  unit: Unit1;
  value: Value1;
}
export interface MeasurementInterval {
  description: Description;
  lower: MeasurementQuantity;
  upper: MeasurementQuantity;
}
export interface CensoredMeasurement {
  kind: Kind2;
  lower: CensorBound | null;
  upper: CensorBound | null;
}
export interface CensorBound {
  inclusive: Inclusive;
  quantity: MeasurementQuantity;
}
export interface CategoricalMeasurement {
  kind: Kind3;
  label: Label;
}
export interface MissingMeasurement {
  kind: Kind4;
  reason: Reason;
}
export interface SeriesDescriptor {
  kind: Kind5;
  point_count: PointCount;
  x_unit: XUnit1;
  y_unit: YUnit;
}
