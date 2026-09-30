/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Limit = number;
export type MaxAttemptsPerActivation = number;
export type ContentSha256 = string;
export type DraftId = string;
export type Revision = number;
export type UniverseSha256 = string;
export type ValidationId = string;
export type Port = string;
export type Value =
  BooleanConstant | IntegerConstant | NumberValue | StringConstant | ArtifactConstant | CollectionValue;
export type Kind = "boolean";
export type Value1 = boolean;
export type Kind1 = "integer";
export type Unit = string;
export type Value2 = number;
export type Kind2 = "number";
export type Unit1 = string;
export type Value3 = string;
export type Kind3 = "string";
export type Value4 = string;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2561 = string;
export type SizeBytes = number;
export type Kind4 = "artifact";
export type Representation = string;
export type Unit2 = string;
export type Kind5 = "missing";
export type MemberId = string;
export type ReasonCode = string;
/**
 * @maxItems 10000
 */
export type Items = (
  (BooleanConstant | IntegerConstant | NumberValue | StringConstant | ArtifactConstant) | MissingValue
)[];
export type Kind6 = "collection";
/**
 * @maxItems 64
 */
export type Inputs = GraphBinding[];
export type DeadlineSeconds = number;
export type MaxActivations = number;
export type PlanSha256 = string;
export type SchemaVersion = "1";

export interface AdmitDraft {
  budget: AttemptBudget;
  draft: DraftSelection;
  inputs: Inputs;
  limits?: GraphLimits;
  plan_sha256: PlanSha256;
  schema_version?: SchemaVersion;
}
export interface AttemptBudget {
  limit: Limit;
  max_attempts_per_activation?: MaxAttemptsPerActivation;
}
export interface DraftSelection {
  content_sha256: ContentSha256;
  draft_id: DraftId;
  revision: Revision;
  universe_sha256: UniverseSha256;
  validation_id: ValidationId;
}
export interface GraphBinding {
  port: Port;
  value: Value;
}
export interface BooleanConstant {
  kind: Kind;
  value: Value1;
}
export interface IntegerConstant {
  kind: Kind1;
  unit?: Unit;
  value: Value2;
}
export interface NumberValue {
  kind: Kind2;
  unit?: Unit1;
  value: Value3;
}
export interface StringConstant {
  kind: Kind3;
  value: Value4;
}
export interface ArtifactConstant {
  artifact: ArtifactRef;
  kind: Kind4;
  representation: Representation;
  unit: Unit2;
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
export interface CollectionValue {
  items: Items;
  kind: Kind6;
}
export interface MissingValue {
  kind: Kind5;
  member_id: MemberId;
  reason_code: ReasonCode;
}
export interface GraphLimits {
  deadline_seconds?: DeadlineSeconds;
  max_activations?: MaxActivations;
}
