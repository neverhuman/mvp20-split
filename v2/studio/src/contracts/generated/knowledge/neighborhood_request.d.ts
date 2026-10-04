/* Generated from the published Python-owned serialization schema. Do not edit. */

export type AssertionLimit = number;
export type EntityLimit = number;
export type EntityId = string;
export type GraphId = string;
export type ProjectId = string;
export type TenantId = string;
export type Revision = number;
export type History = "current" | "retained";
export type AssertionOffset = number;
export type EntityOffset = number;
export type QuerySha256 = string;
export type Radius = number;
export type Revision1 = number;
export type Sha256 = string;
export type WireVersion = "1";

export interface GraphNeighborhoodRequest {
  assertion_limit?: AssertionLimit;
  entity_limit?: EntityLimit;
  focus: EntityRevisionRef;
  history?: History;
  position?: GraphViewPosition | null;
  radius?: Radius;
  revision: DomainRevisionRef;
  wire_version: WireVersion;
}
export interface EntityRevisionRef {
  entity_id: EntityId;
  graph: DomainGraphRef;
  revision: Revision;
}
export interface DomainGraphRef {
  graph_id: GraphId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface GraphViewPosition {
  assertion_offset: AssertionOffset;
  entity_offset: EntityOffset;
  query_sha256: QuerySha256;
}
export interface DomainRevisionRef {
  graph: DomainGraphRef;
  revision: Revision1;
  sha256: Sha256;
}
