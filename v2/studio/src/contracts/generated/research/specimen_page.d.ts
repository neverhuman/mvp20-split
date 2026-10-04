/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Offset = number;
export type QuerySha256 = string;
export type QuerySha2561 = string;
export type ExperimentId = string;
export type Revision = number;
export type ProjectId = string;
export type TenantId = string;
export type Limit = number;
export type WireVersion = "1";
export type CandidateId = string;
export type Revision1 = number;
export type FeatureCount = number;
export type PreparationCount = number;
export type MaterialStateId = string;
export type Revision2 = number;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Sha2561 = string;
export type SizeBytes = number;
export type Revision3 = number;
export type SampleId = string;
export type WireVersion1 = "1";
/**
 * @maxItems 16
 */
export type Rows = SpecimenViewRow[];
export type Total = number;
export type WireVersion2 = "1";

export interface SpecimenViewPage {
  next_position: ResearchViewPosition | null;
  query_sha256: QuerySha2561;
  request: SpecimenViewRequest;
  rows: Rows;
  total: Total;
  wire_version: WireVersion2;
}
export interface ResearchViewPosition {
  offset: Offset;
  query_sha256: QuerySha256;
}
export interface SpecimenViewRequest {
  experiment: ExperimentRevisionRef;
  limit?: Limit;
  position?: ResearchViewPosition | null;
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
export interface SpecimenViewRow {
  material: MaterialStateSummary | null;
  sample: SampleIdentity;
}
export interface MaterialStateSummary {
  candidate: CandidateRevisionRef;
  feature_count: FeatureCount;
  preparation_count: PreparationCount;
  reference: MaterialStateRevisionRef;
  supersedes: MaterialStateRevisionRef | null;
}
export interface CandidateRevisionRef {
  candidate_id: CandidateId;
  revision: Revision1;
  scope: Scope;
}
export interface MaterialStateRevisionRef {
  material_state_id: MaterialStateId;
  revision: Revision2;
  scope: Scope;
}
export interface SampleIdentity {
  candidate: CandidateRevisionRef;
  identity_evidence: ArtifactRef;
  material_state: MaterialStateRevisionRef | null;
  reference: SampleRevisionRef;
  supersedes: SampleRevisionRef | null;
  wire_version: WireVersion1;
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
export interface SampleRevisionRef {
  revision: Revision3;
  sample_id: SampleId;
  scope: Scope;
}
