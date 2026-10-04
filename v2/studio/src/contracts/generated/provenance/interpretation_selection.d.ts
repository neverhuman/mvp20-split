/* Generated from the published Python-owned serialization schema. Do not edit. */

export type InterpretationId = string;
export type Kind = "normalization" | "observation-use";
export type ProjectId = string;
export type TenantId = string;

export interface InterpretationSelection {
  interpretation_id: InterpretationId;
  kind: Kind;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
