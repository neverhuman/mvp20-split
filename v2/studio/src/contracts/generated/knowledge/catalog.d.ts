/* Generated from the published Python-owned serialization schema. Do not edit. */

export type AssertionPage = 128;
export type EntityPage = 64;
export type Radius = 2;
export type ResponseBytes = 1048576;
export type SearchPage = 50;
export type SourceFetch = "separate_data_authority";
export type Owner = "knowledge";
export type GraphId = string;
export type ProjectId = string;
export type TenantId = string;
export type Revision = number;
export type Sha256 = string;
export type SchemaId = string;
export type Sha2561 = string;
export type Version = "1";
export type Version1 = "1";
export type ViewId = "entity_search" | "neighborhood" | "object_detail";
/**
 * @minItems 3
 * @maxItems 3
 */
export type Views = GraphExploreCapability[];
export type WireVersion = "1";

export interface GraphExploreCatalog {
  limits: GraphExploreLimits;
  owner: Owner;
  revision: DomainRevisionRef;
  views: Views;
  wire_version: WireVersion;
}
export interface GraphExploreLimits {
  assertion_page: AssertionPage;
  entity_page: EntityPage;
  radius: Radius;
  response_bytes: ResponseBytes;
  search_page: SearchPage;
  source_fetch: SourceFetch;
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
export interface GraphExploreCapability {
  result_schema: SchemaRef;
  version: Version1;
  view_id: ViewId;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha2561;
  version: Version;
}
