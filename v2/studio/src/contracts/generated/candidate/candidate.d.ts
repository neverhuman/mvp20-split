/* Generated from the published Python-owned serialization schema. Do not edit. */

export type CandidateId = string;
export type Revision = number;
export type ProjectId = string;
export type TenantId = string;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Sha2561 = string;
export type SizeBytes = number;
export type WireVersion = "1";

export interface CandidateRevision {
  reference: CandidateRevisionRef;
  representation: ArtifactRef;
  supersedes: CandidateRevisionRef | null;
  wire_version: WireVersion;
}
export interface CandidateRevisionRef {
  candidate_id: CandidateId;
  revision: Revision;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface ArtifactRef {
  artifact_id: ArtifactId;
  media_type: MediaType;
  schema_ref: SchemaRef;
  scope: Scope;
  sha256: Sha2561;
  size_bytes: SizeBytes;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha256;
  version: Version;
}
