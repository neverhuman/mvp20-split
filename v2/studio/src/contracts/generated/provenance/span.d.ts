/* Generated from the published Python-owned serialization schema. Do not edit. */

export type End = number;
export type Sha256 = string;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha2561 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2562 = string;
export type SizeBytes = number;
export type RevisionId = string;
export type SourceId = string;
export type Start = number;
export type Unit = "byte";

/**
 * Half-open byte range; owner verifies ordering, bounds and exact content.
 */
export interface SourceSpan {
  end: End;
  sha256: Sha256;
  source: SourceRevisionRef;
  start: Start;
  unit: Unit;
}
export interface SourceRevisionRef {
  raw: ArtifactRef;
  revision_id: RevisionId;
  scope: Scope;
  source_id: SourceId;
}
export interface ArtifactRef {
  artifact_id: ArtifactId;
  media_type: MediaType;
  schema_ref: SchemaRef;
  scope: Scope;
  sha256: Sha2562;
  size_bytes: SizeBytes;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha2561;
  version: Version;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
