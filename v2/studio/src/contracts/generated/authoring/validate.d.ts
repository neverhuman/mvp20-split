/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ContentSha256 = string;
export type DraftId = string;
export type Revision = number;
export type SchemaVersion = "1";

export interface ValidateDraft {
  content_sha256: ContentSha256;
  draft_id: DraftId;
  revision: Revision;
  schema_version?: SchemaVersion;
}
