/* Generated from the published Python-owned serialization schema. Do not edit. */

export type EventId = string;
export type Kind = "run_changed";
export type Revision = number;
/**
 * @maxItems 100
 */
export type Entries = GraphInvalidation[];
export type HasMore = boolean;
export type NextCursor = string;
export type ObservedRevision = number;
export type RunId = string;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;

export interface GraphInvalidationPage {
  entries: Entries;
  has_more: HasMore;
  next_cursor: NextCursor;
  observed_revision: ObservedRevision;
  run_id: RunId;
  schema_version?: SchemaVersion;
  scope: Scope;
}
export interface GraphInvalidation {
  event_id: EventId;
  kind?: Kind;
  revision: Revision;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
