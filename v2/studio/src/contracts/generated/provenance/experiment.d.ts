/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ExpectationId = string;
export type CriterionId = string;
export type Kind = "numeric" | "categorical" | "series";
export type Unit = string | null;
export type XUnit = string | null;
export type ReplicateId = string;
export type Role = "sample" | "positive_control" | "negative_control" | "blank";
export type Revision = number;
export type SampleId = string;
export type ProjectId = string;
export type TenantId = string;
/**
 * @minItems 1
 * @maxItems 1024
 */
export type Expectations = ExperimentExpectation[];
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Sha2561 = string;
export type SizeBytes = number;
export type ExperimentId = string;
export type Revision1 = number;
export type CandidateId = string;
export type Revision2 = number;
export type MaterialStateId = string;
export type Revision3 = number;
export type WireVersion = "1";
export type Basis = "measured" | "inferred" | "unknown";
export type Name = string;
export type Value =
  NumericMeasurement | CensoredMeasurement | CategoricalMeasurement | MissingMeasurement | SeriesMeasurement;
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
export type Y = NumericMeasurement | CensoredMeasurement | MissingMeasurement;
/**
 * @minItems 1
 * @maxItems 4096
 */
export type Points = SeriesMeasurementPoint[];
export type XUnit1 = string;
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
export type WireVersion1 = "1";
/**
 * @minItems 1
 * @maxItems 256
 */
export type Samples = ExperimentSample[];
export type WireVersion2 = "1";

export interface ExperimentDefinition {
  expectations: Expectations;
  protocol: ExperimentProtocol;
  reference: ExperimentRevisionRef;
  samples: Samples;
  supersedes: ExperimentRevisionRef | null;
  wire_version: WireVersion2;
}
export interface ExperimentExpectation {
  expectation_id: ExpectationId;
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
  replicate_id: ReplicateId;
  role: Role;
}
export interface SampleRevisionRef {
  revision: Revision;
  sample_id: SampleId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
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
export interface ExperimentRevisionRef {
  experiment_id: ExperimentId;
  revision: Revision1;
  scope: Scope;
}
export interface ExperimentSample {
  sample: SampleIdentity;
  state: MaterialStateRevision | null;
}
export interface SampleIdentity {
  candidate: CandidateRevisionRef;
  identity_evidence: ArtifactRef;
  material_state: MaterialStateRevisionRef | null;
  reference: SampleRevisionRef;
  supersedes: SampleRevisionRef | null;
  wire_version: WireVersion;
}
export interface CandidateRevisionRef {
  candidate_id: CandidateId;
  revision: Revision2;
  scope: Scope;
}
export interface MaterialStateRevisionRef {
  material_state_id: MaterialStateId;
  revision: Revision3;
  scope: Scope;
}
export interface MaterialStateRevision {
  candidate: CandidateRevisionRef;
  features: Features;
  preparation: Preparation;
  reference: MaterialStateRevisionRef;
  supersedes: MaterialStateRevisionRef | null;
  wire_version: WireVersion1;
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
export interface SeriesMeasurement {
  kind: Kind5;
  points: Points;
  x_unit: XUnit1;
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
