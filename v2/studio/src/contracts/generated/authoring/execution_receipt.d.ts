/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Outcome = PendingReceipt | AcceptedReceipt | RejectedReceipt;
export type ActorId = string;
export type CommandFamily = string;
export type CommandId = string;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;
export type OperationId = string;
export type RequestSha256 = string;
export type Status = "pending";
export type Kind = "run" | "attempt" | "completion" | "worker_policy";
export type ObjectId = string;
export type Revision = number;
export type Status1 = "accepted";
export type ReasonCode = string;
export type Status2 = "rejected";
export type SchemaVersion1 = "1";

export interface CommandReceipt {
  outcome: Outcome;
  schema_version?: SchemaVersion1;
}
export interface PendingReceipt {
  binding: ReceiptBinding;
  status: Status;
}
export interface ReceiptBinding {
  identity: CommandIdentity;
  operation_id: OperationId;
  request_sha256: RequestSha256;
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
export interface AcceptedReceipt {
  binding: ReceiptBinding;
  committed: CommittedReference;
  status: Status1;
}
export interface CommittedReference {
  kind: Kind;
  object_id: ObjectId;
  revision: Revision;
}
export interface RejectedReceipt {
  binding: ReceiptBinding;
  reason_code: ReasonCode;
  status: Status2;
}
