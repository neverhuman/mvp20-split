/* Generated from the published Python-owned serialization schema. Do not edit. */

export type AcceptedRunRevision = number;
export type ActivationId = string;
export type CanonicalResult = boolean;
export type CompletionId = string;
export type AttemptId = string;
export type Fence = number;
export type InvocationId = string;
export type Outcome = Succeeded | Abstained | Failed | Uncertain;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2561 = string;
export type SizeBytes = number;
export type Port = string;
/**
 * @minItems 1
 * @maxItems 64
 */
export type Outputs = InputBinding[];
export type Status = "succeeded";
export type ReasonCode = string;
export type Status1 = "abstained";
export type ReasonCode1 = string;
export type Retryable = boolean;
export type Status2 = "failed";
export type OperationId = string;
export type ReasonCode2 = string;
export type Status3 = "uncertain_external_effect";
export type SchemaVersion = "1";
/**
 * @maxItems 65
 */
export type RetentionReservationIds = string[];
export type RunId = string;
export type SchemaVersion1 = "1";

export interface CompletionRecord {
  accepted_run_revision: AcceptedRunRevision;
  activation_id: ActivationId;
  canonical_result: CanonicalResult;
  completion_id: CompletionId;
  result: Completion;
  retention_reservation_ids?: RetentionReservationIds;
  run_id: RunId;
  schema_version?: SchemaVersion1;
  scope: Scope;
}
export interface Completion {
  attempt_id: AttemptId;
  fence: Fence;
  invocation_id: InvocationId;
  outcome: Outcome;
  schema_version: SchemaVersion;
}
export interface Succeeded {
  checkpoint?: ArtifactRef | null;
  outputs: Outputs;
  status: Status;
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
export interface InputBinding {
  artifact: ArtifactRef;
  port: Port;
}
export interface Abstained {
  reason_code: ReasonCode;
  status: Status1;
}
export interface Failed {
  reason_code: ReasonCode1;
  retryable: Retryable;
  status: Status2;
}
export interface Uncertain {
  operation_id: OperationId;
  reason_code: ReasonCode2;
  status: Status3;
}
