/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ActorId = string;
export type Outcome = InterpretationPending | InterpretationComplete;
export type Status = "pending";
export type Projection = NormalizationProjection | ObservationUseProjection;
export type ActorId1 = string;
export type Authority = "policy_interpretation";
export type Kind = "normalization";
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
export type Controls = "passed" | "failed" | "unknown";
/**
 * @maxItems 64
 */
export type Flags = string[];
export type ObservationId = string;
export type Revision3 = number;
export type Value =
  NumericMeasurement | CensoredMeasurement | CategoricalMeasurement | MissingMeasurement | SeriesMeasurement;
export type Kind1 = "numeric";
export type Unit = string;
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
export type XUnit = string;
export type YUnit = string;
export type WireVersion = "1";
export type ProfileId = string;
export type Dimension = string;
export type Scale = string;
export type SourceUnit = string;
export type TargetUnit = string;
/**
 * @minItems 1
 * @maxItems 128
 */
export type Rules = ConversionRuleRecord[];
export type Version1 = string;
export type Kind6 = "normalization";
export type WireVersion1 = "1";
export type InterpretationId = string;
export type Kind7 = "normalization" | "observation-use";
export type Sha2562 = string;
/**
 * @maxItems 2
 */
export type Applied = ConversionRuleRecord[];
export type Normalized =
  (NumericMeasurement | CensoredMeasurement | CategoricalMeasurement | MissingMeasurement | SeriesMeasurement) | null;
export type Original =
  NumericMeasurement | CensoredMeasurement | CategoricalMeasurement | MissingMeasurement | SeriesMeasurement;
export type Reason1 = string | null;
export type Status1 = "normalized" | "unresolved";
export type CoordinateUnit = string | null;
export type ValueUnit = string;
/**
 * @maxItems 128
 */
export type Sources = ArtifactRef[];
export type WireVersion2 = "1";
export type ActorId2 = string;
export type Authority1 = "policy_interpretation";
export type ExpectationId1 = string;
export type CriterionId = string;
export type Kind8 = "numeric" | "categorical" | "series";
export type Unit1 = string | null;
export type XUnit1 = string | null;
export type ReplicateId1 = string;
export type Role1 = "sample" | "positive_control" | "negative_control" | "blank";
/**
 * @minItems 1
 * @maxItems 1024
 */
export type Expectations = ExperimentExpectation[];
export type CandidateId = string;
export type Revision4 = number;
export type WireVersion3 = "1";
export type Basis = "measured" | "inferred" | "unknown";
export type Name = string;
export type Value2 =
  NumericMeasurement | CensoredMeasurement | CategoricalMeasurement | MissingMeasurement | SeriesMeasurement;
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
export type WireVersion4 = "1";
/**
 * @minItems 1
 * @maxItems 256
 */
export type Samples = ExperimentSample[];
export type WireVersion5 = "1";
/**
 * @maxItems 1024
 */
export type Focus = ObservationRevisionRef[];
export type Kind9 = "observation-use";
/**
 * @maxItems 1024
 */
export type MissingExpectations = string[];
export type Kind10 = "observation-use";
export type Action = string;
export type ProfileId1 = string;
export type AvailableValue = boolean;
export type BoundState = boolean;
/**
 * @maxItems 64
 */
export type ExcludedFlags = string[];
export type PassedControls = boolean;
export type Version2 = string;
export type WireVersion6 = "1";
/**
 * @maxItems 64
 */
export type Blockers = string[];
export type Disposition = "usable" | "excluded" | "unresolved" | "quarantined";
export type Disposition1 = "matched" | "quarantined";
/**
 * @maxItems 32
 */
export type Reasons = string[];
export type StateBound = boolean;
/**
 * @maxItems 64
 */
export type Focus1 = string[];
/**
 * @maxItems 64
 */
export type Gaps = string[];
/**
 * @maxItems 1024
 */
export type Reviews = ObservationUseReviewRecord[];
/**
 * @maxItems 128
 */
export type Sources1 = ArtifactRef[];
/**
 * @maxItems 1024
 */
export type Usable = ObservationRevisionRef[];
export type WireVersion7 = "1";
export type Status2 = "interpreted";
export type Request = NormalizeObservationRequest | AssessObservationUseRequest;
export type InterpretationId1 = string;
export type Kind11 = "normalization";
export type Kind12 = "normalization" | "observation-use";
export type WireVersion8 = "1";
export type InterpretationId2 = string;
export type Kind13 = "observation-use";
/**
 * @maxItems 1024
 */
export type Observations = ObservationRevisionRef[];
export type WireVersion9 = "1";
export type WireVersion10 = "1";

export interface InterpretationStatus {
  actor_id: ActorId;
  outcome: Outcome;
  request: Request;
  wire_version: WireVersion10;
}
export interface InterpretationPending {
  status: Status;
}
export interface InterpretationComplete {
  projection: Projection;
  status: Status2;
}
export interface NormalizationProjection {
  actor_id: ActorId1;
  authority: Authority;
  kind: Kind;
  observation: ObservationRevision;
  profile: NormalizationProfile;
  reference: InterpretationRef;
  result: NormalizedMeasurementRecord;
  sources: Sources;
  wire_version: WireVersion2;
}
export interface ObservationRevision {
  binding: ObservationBindingRecord;
  quality: ObservationQuality;
  reference: ObservationRevisionRef;
  source: ArtifactRef;
  supersedes: ObservationRevisionRef | null;
  value: Value;
  wire_version: WireVersion;
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
export interface ObservationQuality {
  controls: Controls;
  flags: Flags;
}
export interface ObservationRevisionRef {
  observation_id: ObservationId;
  revision: Revision3;
  scope: Scope;
}
export interface NumericMeasurement {
  kind: Kind1;
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
  x_unit: XUnit;
  y_unit: YUnit;
}
export interface SeriesMeasurementPoint {
  x: MeasurementQuantity;
  y: Y;
}
export interface NormalizationProfile {
  catalog: ConversionCatalogRecord;
  kind: Kind6;
  scope: Scope;
  wire_version: WireVersion1;
}
export interface ConversionCatalogRecord {
  profile_id: ProfileId;
  reference: SchemaRef;
  rules: Rules;
  version: Version1;
}
export interface ConversionRuleRecord {
  dimension: Dimension;
  scale: Scale;
  source_unit: SourceUnit;
  target_unit: TargetUnit;
}
export interface InterpretationRef {
  interpretation_id: InterpretationId;
  kind: Kind7;
  scope: Scope;
  sha256: Sha2562;
}
export interface NormalizedMeasurementRecord {
  applied: Applied;
  normalized: Normalized;
  original: Original;
  policy: SchemaRef;
  reason: Reason1;
  status: Status1;
  targets: NormalizationTargetRecord;
}
export interface NormalizationTargetRecord {
  coordinate_unit: CoordinateUnit;
  value_unit: ValueUnit;
}
export interface ObservationUseProjection {
  actor_id: ActorId2;
  authority: Authority1;
  experiment: ExperimentDefinition;
  focus: Focus;
  kind: Kind9;
  missing_expectations: MissingExpectations;
  profile: ObservationUseProfile;
  reference: InterpretationRef;
  reviews: Reviews;
  sources: Sources1;
  usable: Usable;
  wire_version: WireVersion7;
}
export interface ExperimentDefinition {
  expectations: Expectations;
  protocol: ExperimentProtocol;
  reference: ExperimentRevisionRef;
  samples: Samples;
  supersedes: ExperimentRevisionRef | null;
  wire_version: WireVersion5;
}
export interface ExperimentExpectation {
  expectation_id: ExpectationId1;
  readout: ExperimentReadout;
  replicate: ExperimentReplicate;
  sample: SampleRevisionRef;
}
export interface ExperimentReadout {
  criterion_id: CriterionId;
  kind: Kind8;
  unit: Unit1;
  x_unit: XUnit1;
}
export interface ExperimentReplicate {
  replicate_id: ReplicateId1;
  role: Role1;
}
export interface ExperimentProtocol {
  applicability: ArtifactRef;
  method: SchemaRef;
  source: ArtifactRef;
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
  wire_version: WireVersion3;
}
export interface CandidateRevisionRef {
  candidate_id: CandidateId;
  revision: Revision4;
  scope: Scope;
}
export interface MaterialStateRevision {
  candidate: CandidateRevisionRef;
  features: Features;
  preparation: Preparation;
  reference: MaterialStateRevisionRef;
  supersedes: MaterialStateRevisionRef | null;
  wire_version: WireVersion4;
}
export interface MaterialFeatureRecord {
  evidence: MaterialFeatureEvidence;
  name: Name;
  value: Value2;
}
export interface MaterialFeatureEvidence {
  basis: Basis;
  method: SchemaRef | null;
  source: ArtifactRef | null;
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
export interface ObservationUseProfile {
  kind: Kind10;
  policy: ObservationUsePolicyRecord;
  scope: Scope;
  wire_version: WireVersion6;
}
export interface ObservationUsePolicyRecord {
  action: Action;
  normalization: ConversionCatalogRecord | null;
  profile_id: ProfileId1;
  reference: SchemaRef;
  requirements: ObservationUseRequirements;
  version: Version2;
}
export interface ObservationUseRequirements {
  available_value: AvailableValue;
  bound_state: BoundState;
  excluded_flags: ExcludedFlags;
  passed_controls: PassedControls;
}
export interface ObservationUseReviewRecord {
  blockers: Blockers;
  disposition: Disposition;
  effective_match: InterpretationMatchRecord;
  focus: Focus1;
  gaps: Gaps;
  normalization: NormalizedMeasurementRecord | null;
  observation: ObservationRevision;
  raw_match: InterpretationMatchRecord;
}
export interface InterpretationMatchRecord {
  disposition: Disposition1;
  reasons: Reasons;
  state_bound: StateBound;
}
export interface NormalizeObservationRequest {
  interpretation_id: InterpretationId1;
  kind: Kind11;
  observation: ObservationRevisionRef;
  profile: InterpretationProfileRef;
  targets: NormalizationTargetRecord;
  wire_version: WireVersion8;
}
export interface InterpretationProfileRef {
  kind: Kind12;
  policy: SchemaRef;
  scope: Scope;
}
export interface AssessObservationUseRequest {
  experiment: ExperimentRevisionRef;
  interpretation_id: InterpretationId2;
  kind: Kind13;
  observations: Observations;
  profile: InterpretationProfileRef;
  wire_version: WireVersion9;
}
