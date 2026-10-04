/* Generated from the published Python-owned serialization schema. Do not edit. */

/**
 * @minItems 1
 * @maxItems 32
 */
export type CriterionIds = string[];
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type QuestionId = string;
export type Revision = number;
export type ProjectId = string;
export type TenantId = string;
export type NeedId = string;
export type Revision1 = number;
export type ArtifactId = string;
export type MediaType = string;
export type Sha2561 = string;
export type SizeBytes = number;
export type WireVersion = "1";

export interface EvidenceNeed {
  criterion_ids: CriterionIds;
  method: SchemaRef;
  question: ResearchQuestionRef;
  reference: EvidenceNeedRef;
  required_context: ArtifactRef;
  supersedes: EvidenceNeedRef | null;
  wire_version: WireVersion;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha256;
  version: Version;
}
export interface ResearchQuestionRef {
  question_id: QuestionId;
  revision: Revision;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface EvidenceNeedRef {
  need_id: NeedId;
  revision: Revision1;
  scope: Scope;
}
export interface ArtifactRef {
  artifact_id: ArtifactId;
  media_type: MediaType;
  schema_ref: SchemaRef;
  scope: Scope;
  sha256: Sha2561;
  size_bytes: SizeBytes;
}
