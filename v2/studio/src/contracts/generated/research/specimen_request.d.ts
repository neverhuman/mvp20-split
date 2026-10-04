/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ExperimentId = string;
export type Revision = number;
export type ProjectId = string;
export type TenantId = string;
export type Limit = number;
export type Offset = number;
export type QuerySha256 = string;
export type WireVersion = "1";

export interface SpecimenViewRequest {
  experiment: ExperimentRevisionRef;
  limit?: Limit;
  position?: ResearchViewPosition | null;
  wire_version: WireVersion;
}
export interface ExperimentRevisionRef {
  experiment_id: ExperimentId;
  revision: Revision;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface ResearchViewPosition {
  offset: Offset;
  query_sha256: QuerySha256;
}
