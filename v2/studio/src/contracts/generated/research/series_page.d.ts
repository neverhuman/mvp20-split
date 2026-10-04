/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2561 = string;
export type SizeBytes = number;
export type Role = ("sample" | "positive_control" | "negative_control" | "blank") | null;
export type MaterialStateId = string;
export type Revision = number;
export type Revision1 = number;
export type SampleId = string;
export type ExpectationId = string | null;
export type ExperimentId = string;
export type Revision2 = number;
export type ReplicateId = string | null;
export type Offset = number;
export type QuerySha256 = string;
export type Unit = string;
export type Value = string;
export type Y = NumericMeasurement | CensoredMeasurement | MissingMeasurement;
export type Kind = "numeric";
export type Description = string;
export type Kind1 = "censored";
export type Inclusive = boolean;
export type Kind2 = "missing";
export type Reason = string;
/**
 * @maxItems 256
 */
export type Points = SeriesMeasurementPoint[];
export type Controls = "passed" | "failed" | "unknown";
/**
 * @maxItems 64
 */
export type Flags = string[];
export type QuerySha2561 = string;
export type Limit = number;
export type ObservationId = string;
export type Revision3 = number;
export type WireVersion = "1";
export type Total = number;
export type WireVersion1 = "1";
export type XUnit = string;
export type YUnit = string;

export interface ObservationSeriesPage {
  binding: ObservationBindingRecord;
  next_position: ResearchViewPosition | null;
  points: Points;
  quality: ObservationQuality;
  query_sha256: QuerySha2561;
  request: ObservationSeriesRequest;
  source: ArtifactRef;
  total: Total;
  wire_version: WireVersion1;
  x_unit: XUnit;
  y_unit: YUnit;
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
export interface ObservationSpecimen {
  material_state: MaterialStateRevisionRef | null;
  sample: SampleRevisionRef | null;
}
export interface MaterialStateRevisionRef {
  material_state_id: MaterialStateId;
  revision: Revision;
  scope: Scope;
}
export interface SampleRevisionRef {
  revision: Revision1;
  sample_id: SampleId;
  scope: Scope;
}
export interface ObservationTarget {
  expectation_id: ExpectationId;
  experiment: ExperimentRevisionRef | null;
  replicate_id: ReplicateId;
}
export interface ExperimentRevisionRef {
  experiment_id: ExperimentId;
  revision: Revision2;
  scope: Scope;
}
export interface ResearchViewPosition {
  offset: Offset;
  query_sha256: QuerySha256;
}
export interface SeriesMeasurementPoint {
  x: MeasurementQuantity;
  y: Y;
}
export interface MeasurementQuantity {
  unit: Unit;
  value: Value;
}
export interface NumericMeasurement {
  kind: Kind;
  quantity: MeasurementQuantity;
  uncertainty: MeasurementInterval | null;
}
export interface MeasurementInterval {
  description: Description;
  lower: MeasurementQuantity;
  upper: MeasurementQuantity;
}
export interface CensoredMeasurement {
  kind: Kind1;
  lower: CensorBound | null;
  upper: CensorBound | null;
}
export interface CensorBound {
  inclusive: Inclusive;
  quantity: MeasurementQuantity;
}
export interface MissingMeasurement {
  kind: Kind2;
  reason: Reason;
}
export interface ObservationQuality {
  controls: Controls;
  flags: Flags;
}
export interface ObservationSeriesRequest {
  limit?: Limit;
  observation: ObservationRevisionRef;
  position?: ResearchViewPosition | null;
  wire_version: WireVersion;
}
export interface ObservationRevisionRef {
  observation_id: ObservationId;
  revision: Revision3;
  scope: Scope;
}
