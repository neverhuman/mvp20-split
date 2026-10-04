/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2561 = string;
export type SizeBytes = number;
export type CriterionId = string;
export type Description = string;
/**
 * @minItems 1
 * @maxItems 32
 */
export type Criteria = AnswerCriterion[];
export type Objective = string;
export type QuestionId = string;
export type Revision = number;
export type WireVersion = "1";

export interface ResearchQuestion {
  applicability: ArtifactRef;
  criteria: Criteria;
  objective: Objective;
  reference: ResearchQuestionRef;
  supersedes: ResearchQuestionRef | null;
  wire_version: WireVersion;
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
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface AnswerCriterion {
  criterion_id: CriterionId;
  description: Description;
}
export interface ResearchQuestionRef {
  question_id: QuestionId;
  revision: Revision;
  scope: Scope;
}
