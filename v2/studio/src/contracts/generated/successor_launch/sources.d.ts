/* Generated from the published Python-owned serialization schema. Do not edit. */

export type PlanSha256 = string;
export type Revision = number;
export type RunId = string;
export type PredecessorReady = boolean;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;
export type Source = RunOutputSource | NodeOutputSource;
export type Kind = "run_output";
export type Port = string;
export type ActivationId = string;
export type Kind1 = "node_output";
export type Port1 = string;
export type ValueSha256 = string;
/**
 * @maxItems 64
 */
export type Sources = CarrySourceView[];

export interface CarrySources {
  predecessor: PredecessorCut;
  predecessor_ready: PredecessorReady;
  schema_version?: SchemaVersion;
  scope: Scope;
  sources: Sources;
}
export interface PredecessorCut {
  plan_sha256: PlanSha256;
  revision: Revision;
  run_id: RunId;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface CarrySourceView {
  source: Source;
  value_sha256: ValueSha256;
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
