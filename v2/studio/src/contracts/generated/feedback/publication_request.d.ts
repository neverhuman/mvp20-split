/* Generated from the published Python-owned serialization schema. Do not edit. */

export type AssessmentId = string;
export type ProjectId = string;
export type TenantId = string;
export type WireVersion = "1";

export interface AssessmentPublicationRequest {
  assessment_id: AssessmentId;
  scope: Scope;
  wire_version: WireVersion;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
