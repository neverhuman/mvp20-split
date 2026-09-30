/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ContentSha256 = string;
export type DraftId = string;
export type Revision = number;
export type Title = string;
/**
 * @maxItems 50
 */
export type Drafts = DraftHead[];
export type NextAfter = string | null;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;

export interface DraftPage {
  drafts: Drafts;
  next_after: NextAfter;
  schema_version?: SchemaVersion;
  scope: Scope;
}
export interface DraftHead {
  content_sha256: ContentSha256;
  draft_id: DraftId;
  revision: Revision;
  title: Title;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
