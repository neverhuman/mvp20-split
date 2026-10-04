/* Generated from the published Python-owned serialization schema. Do not edit. */

export type EntityId = string;
export type GraphId = string;
export type ProjectId = string;
export type TenantId = string;
export type Revision = number;
export type EntityType = string;
export type IsLatest = boolean;
export type Label = string;
/**
 * @maxItems 50
 */
export type Entities = GraphEntitySummary[];
export type AssertionOffset = number;
export type EntityOffset = number;
export type QuerySha256 = string;
export type QuerySha2561 = string;
export type EntityType1 = string | null;
export type History = "current" | "retained";
export type Limit = number;
export type Revision1 = number;
export type Sha256 = string;
export type Text = string;
export type WireVersion = "1";
export type Total = number;
export type WireVersion1 = "1";

export interface GraphEntitySearchPage {
  entities: Entities;
  next_position: GraphViewPosition | null;
  query_sha256: QuerySha2561;
  request: GraphEntitySearchRequest;
  total: Total;
  wire_version: WireVersion1;
}
export interface GraphEntitySummary {
  alias_target: EntityRevisionRef | null;
  entity_type: EntityType;
  is_latest: IsLatest;
  label: Label;
  reference: EntityRevisionRef;
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
export interface GraphEntitySearchRequest {
  entity_type?: EntityType1;
  history?: History;
  limit?: Limit;
  position?: GraphViewPosition | null;
  revision: DomainRevisionRef;
  text?: Text;
  wire_version: WireVersion;
}
export interface DomainRevisionRef {
  graph: DomainGraphRef;
  revision: Revision1;
  sha256: Sha256;
}
