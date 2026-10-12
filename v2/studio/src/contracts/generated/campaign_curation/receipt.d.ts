/* Generated from the published Python-owned serialization schema. Do not edit. */

export type CreatedAt = string;
export type ActorId = string;
export type CommandFamily = string;
export type CommandId = string;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;
export type Phase =
  | "queued"
  | "assembling"
  | "awaiting_provider"
  | "proposed"
  | "abstained"
  | "compiling"
  | "ready"
  | "failed"
  | "indeterminate";
export type ReasonCode = string | null;
export type CurationId = string;
export type RequestSha256 = string;
export type Revision = number;
export type UpdatedAt = string;
export type WireVersion = "1";

export interface CurationReceipt {
  created_at: CreatedAt;
  identity: CommandIdentity;
  phase: Phase;
  reason_code: ReasonCode;
  reference: CurationRef;
  request_sha256: RequestSha256;
  revision: Revision;
  updated_at: UpdatedAt;
  wire_version?: WireVersion;
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
export interface CurationRef {
  curation_id: CurationId;
  scope: Scope;
}
