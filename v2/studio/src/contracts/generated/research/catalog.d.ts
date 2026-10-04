/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ExperimentId = string;
export type Revision = number;
export type ProjectId = string;
export type TenantId = string;
export type ResponseBytes = 1048576;
export type Rows = 16;
export type SelectedObservations = 128;
export type SeriesPoints = 256;
export type SourceFetch = "separate_data_authority";
export type Owner = "research";
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Version1 = "1";
export type ViewId = "specimens" | "properties" | "observation_series";
/**
 * @minItems 3
 * @maxItems 3
 */
export type Views = ResearchViewCapability[];
export type WireVersion = "1";

export interface ResearchViewCatalog {
  experiment: ExperimentRevisionRef;
  limits: ResearchViewLimits;
  owner: Owner;
  views: Views;
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
export interface ResearchViewLimits {
  response_bytes: ResponseBytes;
  rows: Rows;
  selected_observations: SelectedObservations;
  series_points: SeriesPoints;
  source_fetch: SourceFetch;
}
export interface ResearchViewCapability {
  result_schema: SchemaRef;
  version: Version1;
  view_id: ViewId;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha256;
  version: Version;
}
