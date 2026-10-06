/* Generated from the published Python-owned serialization schema. Do not edit. */

export type CheckpointSeedSha256 = string;
export type Outcome = CheckpointPending | CheckpointModelAccepted | CheckpointFallback | CheckpointCancelled;
export type Kind = "pending";
export type RequestSha256 = string | null;
export type Stage = "checkpoint" | "requested" | "dispatched" | "proposed";
export type Effect = AppliedFields | RetainedProposal | ContinuedUnchanged;
export type FieldName = string;
export type PreviousValueSha256 = string;
export type Value = BooleanConstant | IntegerConstant | NumberValue | StringConstant;
export type Kind1 = "boolean";
export type Value1 = boolean;
export type Kind2 = "integer";
export type Unit = string;
export type Value2 = number;
export type Kind3 = "number";
export type Unit1 = string;
export type Value3 = string;
export type Kind4 = "string";
export type Value4 = string;
/**
 * @minItems 1
 * @maxItems 64
 */
export type Changes = EffectiveFieldChange[];
export type Kind5 = "adjusted_materialization_fields";
export type SelectionSha256 = string;
export type NodeId = string;
export type Index = number;
export type Kind6 = "loop";
export type NodeId1 = string;
export type Index1 = number;
export type Kind7 = "scatter";
export type MembershipSha256 = string;
export type NodeId2 = string;
/**
 * @maxItems 16
 */
export type Occurrences = (LoopOccurrence | ScatterOccurrence)[];
export type SchemaVersion = "2";
export type ContentSha256 = string;
export type Kind8 = "future_campaign" | "evidence_request" | "abstained";
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2561 = string;
export type SizeBytes = number;
export type Kind9 = "continued";
export type Kind10 = "model_accepted";
export type RequestSha2561 = string;
export type ResponseSha256 = string;
export type Action = "continue_unchanged" | "block_target";
export type Kind11 = "fallback";
export type ReasonCode = string;
export type Kind12 = "cancelled";
export type ReasonCode1 = string;
export type Profile = "checkpoint-decision.v1";
export type DecisionId = string;
export type RunId = string;
export type Revision = number;
export type SchemaVersion1 = "1";

export interface CheckpointDecision {
  checkpoint_seed_sha256: CheckpointSeedSha256;
  outcome: Outcome;
  profile?: Profile;
  reference: SupervisionRef;
  revision: Revision;
  schema_version?: SchemaVersion1;
}
export interface CheckpointPending {
  kind: Kind;
  request_sha256: RequestSha256;
  stage: Stage;
}
export interface CheckpointModelAccepted {
  effect: Effect;
  kind: Kind10;
  request_sha256: RequestSha2561;
  response_sha256: ResponseSha256;
}
export interface AppliedFields {
  changes: Changes;
  kind: Kind5;
  selection_sha256: SelectionSha256;
  target: ActivationPath;
}
export interface EffectiveFieldChange {
  field_name: FieldName;
  previous_value_sha256: PreviousValueSha256;
  value: Value;
}
export interface BooleanConstant {
  kind: Kind1;
  value: Value1;
}
export interface IntegerConstant {
  kind: Kind2;
  unit?: Unit;
  value: Value2;
}
export interface NumberValue {
  kind: Kind3;
  unit?: Unit1;
  value: Value3;
}
export interface StringConstant {
  kind: Kind4;
  value: Value4;
}
export interface ActivationPath {
  node_id: NodeId;
  occurrences?: Occurrences;
  schema_version: SchemaVersion;
}
export interface LoopOccurrence {
  index: Index;
  kind: Kind6;
  node_id: NodeId1;
}
export interface ScatterOccurrence {
  index: Index1;
  kind: Kind7;
  membership_sha256: MembershipSha256;
  node_id: NodeId2;
}
export interface RetainedProposal {
  content_sha256: ContentSha256;
  kind: Kind8;
  proposal: ArtifactRef;
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
export interface ContinuedUnchanged {
  kind: Kind9;
}
export interface CheckpointFallback {
  action: Action;
  kind: Kind11;
  reason_code: ReasonCode;
}
export interface CheckpointCancelled {
  kind: Kind12;
  reason_code: ReasonCode1;
}
export interface SupervisionRef {
  decision_id: DecisionId;
  run_id: RunId;
  scope: Scope;
}
