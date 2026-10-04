/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ExperimentId = string;
export type Revision = number;
export type ProjectId = string;
export type TenantId = string;
export type Limit = number;
export type ObservationId = string;
export type Revision1 = number;
/**
 * @minItems 1
 * @maxItems 128
 */
export type Observations = ObservationRevisionRef[];
export type Offset = number;
export type QuerySha256 = string;
export type WireVersion = "1";

export interface PropertyViewRequest {
  experiment: ExperimentRevisionRef;
  limit?: Limit;
  observations: Observations;
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
export interface ObservationRevisionRef {
  observation_id: ObservationId;
  revision: Revision1;
  scope: Scope;
}
export interface ResearchViewPosition {
  offset: Offset;
  query_sha256: QuerySha256;
}
