/* Generated from the published Python-owned serialization schema. Do not edit. */

export type EntityType = string | null;
export type History = "current" | "retained";
export type Limit = number;
export type AssertionOffset = number;
export type EntityOffset = number;
export type QuerySha256 = string;
export type GraphId = string;
export type ProjectId = string;
export type TenantId = string;
export type Revision = number;
export type Sha256 = string;
export type Text = string;
export type WireVersion = "1";

export interface GraphEntitySearchRequest {
  entity_type?: EntityType;
  history?: History;
  limit?: Limit;
  position?: GraphViewPosition | null;
  revision: DomainRevisionRef;
  text?: Text;
  wire_version: WireVersion;
}
export interface GraphViewPosition {
  assertion_offset: AssertionOffset;
  entity_offset: EntityOffset;
  query_sha256: QuerySha256;
}
export interface DomainRevisionRef {
  graph: DomainGraphRef;
  revision: Revision;
  sha256: Sha256;
}
export interface DomainGraphRef {
  graph_id: GraphId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
