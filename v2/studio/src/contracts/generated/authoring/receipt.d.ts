/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Outcome = DraftAccepted | DraftRejected | DraftPending;
export type ActorId = string;
export type CommandFamily = string;
export type CommandId = string;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;
export type OperationId = string;
export type RequestSha256 = string;
export type ContentSha256 = string;
export type Kind = "draft_revision" | "draft_validation";
export type ObjectId = string;
export type Revision = number;
export type Status = "accepted";
export type ReasonCode = string;
export type Status1 = "rejected";
export type Status2 = "pending";
export type SchemaVersion1 = "1";

export interface DraftCommandReceipt {
  outcome: Outcome;
  schema_version?: SchemaVersion1;
}
export interface DraftAccepted {
  binding: DraftReceiptBinding;
  committed: DraftCommit;
  status: Status;
}
export interface DraftReceiptBinding {
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
export interface DraftCommit {
  content_sha256: ContentSha256;
  kind: Kind;
  object_id: ObjectId;
  revision: Revision;
}
export interface DraftRejected {
  binding: DraftReceiptBinding;
  reason_code: ReasonCode;
  status: Status1;
}
export interface DraftPending {
  binding: DraftReceiptBinding;
  status: Status2;
}
