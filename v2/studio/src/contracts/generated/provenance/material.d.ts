/* Generated from the published Python-owned serialization schema. Do not edit. */

export type CandidateId = string;
export type Revision = number;
export type ProjectId = string;
export type TenantId = string;
export type Basis = "measured" | "inferred" | "unknown";
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type ArtifactId = string;
export type MediaType = string;
export type Sha2561 = string;
export type SizeBytes = number;
export type Name = string;
export type Value =
  NumericMeasurement | CensoredMeasurement | CategoricalMeasurement | MissingMeasurement | SeriesMeasurement;
export type Kind = "numeric";
export type Unit = string;
export type Value1 = string;
export type Description = string;
export type Kind1 = "censored";
export type Inclusive = boolean;
export type Kind2 = "categorical";
export type Label = string;
export type Kind3 = "missing";
export type Reason = string;
export type Kind4 = "series";
export type Y = NumericMeasurement | CensoredMeasurement | MissingMeasurement;
/**
 * @minItems 1
 * @maxItems 4096
 */
export type Points = SeriesMeasurementPoint[];
export type XUnit = string;
export type YUnit = string;
/**
 * @maxItems 128
 */
export type Features = MaterialFeatureRecord[];
export type Actor = string;
export type Basis1 = "proposed" | "observed";
export type Equipment = string[] | null;
export type Atmosphere = string | null;
export type Name1 = string;
/**
 * @maxItems 64
 */
export type Conditions = ProcessingCondition[];
export type EventId = string;
/**
 * @maxItems 256
 */
export type Preparation = ProcessingEventRecord[];
export type MaterialStateId = string;
export type Revision1 = number;
export type WireVersion = "1";

export interface MaterialStateRevision {
  candidate: CandidateRevisionRef;
  features: Features;
  preparation: Preparation;
  reference: MaterialStateRevisionRef;
  supersedes: MaterialStateRevisionRef | null;
  wire_version: WireVersion;
}
export interface CandidateRevisionRef {
  candidate_id: CandidateId;
  revision: Revision;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface MaterialFeatureRecord {
  evidence: MaterialFeatureEvidence;
  name: Name;
  value: Value;
}
export interface MaterialFeatureEvidence {
  basis: Basis;
  method: SchemaRef | null;
  source: ArtifactRef | null;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha256;
  version: Version;
}
export interface ArtifactRef {
  artifact_id: ArtifactId;
  media_type: MediaType;
  schema_ref: SchemaRef;
  scope: Scope;
  sha256: Sha2561;
  size_bytes: SizeBytes;
}
export interface NumericMeasurement {
  kind: Kind;
  quantity: MeasurementQuantity;
  uncertainty: MeasurementInterval | null;
}
export interface MeasurementQuantity {
  unit: Unit;
  value: Value1;
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
export interface CategoricalMeasurement {
  kind: Kind2;
  label: Label;
}
export interface MissingMeasurement {
  kind: Kind3;
  reason: Reason;
}
export interface SeriesMeasurement {
  kind: Kind4;
  points: Points;
  x_unit: XUnit;
  y_unit: YUnit;
}
export interface SeriesMeasurementPoint {
  x: MeasurementQuantity;
  y: Y;
}
export interface ProcessingEventRecord {
  attribution: ProcessingAttribution;
  context: ProcessingContextRecord;
  event_id: EventId;
}
export interface ProcessingAttribution {
  actor: Actor;
  basis: Basis1;
  equipment: Equipment;
  source: ArtifactRef;
}
export interface ProcessingContextRecord {
  atmosphere: Atmosphere;
  conditions: Conditions;
  duration: MeasurementQuantity | null;
  method: SchemaRef;
}
export interface ProcessingCondition {
  name: Name1;
  quantity: MeasurementQuantity;
}
export interface MaterialStateRevisionRef {
  material_state_id: MaterialStateId;
  revision: Revision1;
  scope: Scope;
}
