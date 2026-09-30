/* Generated from the published Python-owned serialization schema. Do not edit. */

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
export type PlanSha256 = string;
export type PlanSha2561 = string;
export type Revision = number;
export type RunId = string;
export type RunId1 = string;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;
export type TransferSha256 = string;

export interface SuccessorLineage {
  carried: Carried;
  plan_sha256: PlanSha256;
  predecessor: PredecessorCut;
  run_id: RunId1;
  schema_version?: SchemaVersion;
  scope: Scope;
  transfer_sha256: TransferSha256;
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
export interface PredecessorCut {
  plan_sha256: PlanSha2561;
  revision: Revision;
  run_id: RunId;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
