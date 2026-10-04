/* Generated from the published Python-owned serialization schema. Do not edit. */

export type InterpretationId = string;
export type Kind = "normalization" | "observation-use";
export type ProjectId = string;
export type TenantId = string;
export type Sha256 = string;

export interface InterpretationRef {
  interpretation_id: InterpretationId;
  kind: Kind;
  scope: Scope;
  sha256: Sha256;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
