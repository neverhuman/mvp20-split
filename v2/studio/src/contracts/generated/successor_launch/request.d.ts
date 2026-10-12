/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Encoding = "amphora-command-v2";
export type ActorId = string;
export type CommandFamily = string;
export type CommandId = string;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;
export type Encoding1 = "amphora-command-v2";
export type Limit = number;
export type MaxAttemptsPerActivation = number;
export type ExpectedValueSha256 = string;
export type Source = RunOutputSource | NodeOutputSource;
export type Kind = "run_output";
export type Port = string;
export type ActivationId = string;
export type Kind1 = "node_output";
export type Port1 = string;
export type TargetPort = string;
/**
 * @maxItems 64
 */
export type Carried = CarriedBinding[];
export type ContentSha256 = string;
export type DraftId = string;
export type Revision = number;
export type UniverseSha256 = string;
export type ValidationId = string;
export type Port2 = string;
export type Value =
  BooleanConstant | IntegerConstant | NumberValue | StringConstant | ArtifactConstant | CollectionValue;
export type Kind2 = "boolean";
export type Value1 = boolean;
export type Kind3 = "integer";
export type Unit = string;
export type Value2 = number;
export type Kind4 = "number";
export type Unit1 = string;
export type Value3 = string;
export type Kind5 = "string";
export type Value4 = string;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Sha2561 = string;
export type SizeBytes = number;
export type Kind6 = "artifact";
export type Representation = string;
export type Unit2 = string;
export type Kind7 = "missing";
export type MemberId = string;
export type ReasonCode = string;
/**
 * @maxItems 10000
 */
export type Items = (
  (BooleanConstant | IntegerConstant | NumberValue | StringConstant | ArtifactConstant) | MissingValue
)[];
export type Kind8 = "collection";
/**
 * @maxItems 64
 */
export type Inputs = GraphBinding[];
export type DeadlineSeconds = number;
export type MaxActivations = number;
export type PlanSha256 = string;
export type PlanSha2561 = string;
export type Revision1 = number;
export type RunId = string;
export type SchemaVersion1 = "1";
export type ProfileId = string;
export type Sha2562 = string;
export type Version1 = "1";

export interface SuccessorLaunchRequest {
  encoding: Encoding;
  identity: CommandIdentity;
  payload: SuccessorLaunchSpecification;
}
export interface CommandIdentity {
  actor_id: ActorId;
  command_family: CommandFamily;
  command_id: CommandId;
  schema_version?: SchemaVersion;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface SuccessorLaunchSpecification {
  admission: SuccessorAdmission;
  profile: LaunchProfileRef;
}
export interface SuccessorAdmission {
  encoding: Encoding1;
  identity: CommandIdentity;
  payload: AdmitDraftSuccessor;
}
export interface AdmitDraftSuccessor {
  budget: AttemptBudget;
  carried: Carried;
  draft: DraftSelection;
  inputs: Inputs;
  limits?: GraphLimits;
  plan_sha256: PlanSha256;
  predecessor: PredecessorCut;
  schema_version?: SchemaVersion1;
}
export interface AttemptBudget {
  limit: Limit;
  max_attempts_per_activation?: MaxAttemptsPerActivation;
}
export interface CarriedBinding {
  expected_value_sha256: ExpectedValueSha256;
  source: Source;
  target_port: TargetPort;
}
export interface RunOutputSource {
  kind?: Kind;
  port: Port;
}
export interface NodeOutputSource {
  activation_id: ActivationId;
  kind?: Kind1;
  port: Port1;
}
export interface DraftSelection {
  content_sha256: ContentSha256;
  draft_id: DraftId;
  revision: Revision;
  universe_sha256: UniverseSha256;
  validation_id: ValidationId;
}
export interface GraphBinding {
  port: Port2;
  value: Value;
}
export interface BooleanConstant {
  kind: Kind2;
  value: Value1;
}
export interface IntegerConstant {
  kind: Kind3;
  unit?: Unit;
  value: Value2;
}
export interface NumberValue {
  kind: Kind4;
  unit?: Unit1;
  value: Value3;
}
export interface StringConstant {
  kind: Kind5;
  value: Value4;
}
export interface ArtifactConstant {
  artifact: ArtifactRef;
  kind: Kind6;
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
export interface CollectionValue {
  items: Items;
  kind: Kind8;
}
export interface MissingValue {
  kind: Kind7;
  member_id: MemberId;
  reason_code: ReasonCode;
}
export interface GraphLimits {
  deadline_seconds?: DeadlineSeconds;
  max_activations?: MaxActivations;
}
export interface PredecessorCut {
  plan_sha256: PlanSha2561;
  revision: Revision1;
  run_id: RunId;
}
export interface LaunchProfileRef {
  profile_id: ProfileId;
  sha256: Sha2562;
  version: Version1;
}
