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
/**
 * @maxItems 32
 */
export type Answers = AssessmentAnswerRef[];
export type AssessmentId = string;
export type ProfileId = string;
export type Sha2562 = string;
export type Version1 = string;
export type QuestionId = string;
export type Revision = number;
/**
 * @maxItems 256
 */
export type Receipts = ArtifactRef[];
export type WireVersion = "1";

export interface EvidenceAssessmentRequest {
  answers: Answers;
  assessment_id: AssessmentId;
  profile: AssessmentProfileRef;
  question: ResearchQuestionRef;
  receipts: Receipts;
  wire_version: WireVersion;
}
export interface AssessmentAnswerRef {
  artifact: ArtifactRef;
  criterion_id: CriterionId;
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
export interface AssessmentProfileRef {
  profile_id: ProfileId;
  scope: Scope;
  sha256: Sha2562;
  version: Version1;
}
export interface ResearchQuestionRef {
  question_id: QuestionId;
  revision: Revision;
  scope: Scope;
}
