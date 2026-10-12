/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ActorId = string;
export type CommandFamily = string;
export type CommandId = string;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;
export type RequestSha256 = string;

export interface SuccessorLaunchReceiptQuery {
  identity: CommandIdentity;
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
