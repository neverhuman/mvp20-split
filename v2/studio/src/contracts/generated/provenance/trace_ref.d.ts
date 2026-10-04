/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ProjectId = string;
export type TenantId = string;
export type Sha256 = string;
export type TraceId = string;

export interface ConversionTraceRef {
  scope: Scope;
  sha256: Sha256;
  trace_id: TraceId;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
