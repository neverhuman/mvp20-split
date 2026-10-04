/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Limit = number;
export type ObservationId = string;
export type Revision = number;
export type ProjectId = string;
export type TenantId = string;
export type Offset = number;
export type QuerySha256 = string;
export type WireVersion = "1";

export interface ObservationSeriesRequest {
  limit?: Limit;
  observation: ObservationRevisionRef;
  position?: ResearchViewPosition | null;
  wire_version: WireVersion;
}
export interface ObservationRevisionRef {
  observation_id: ObservationId;
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
