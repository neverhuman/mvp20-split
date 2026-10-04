/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ActorId = string;
export type Outcome = PendingAssessment | FailedAssessment | CompletedAssessment;
export type Status = "pending";
export type Code = string;
export type Status1 = "failed";
export type ActorId1 = string;
export type Answered = boolean;
export type Authority = "synthetic";
export type Disposition = "supported" | "contradicted" | "unknown";
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2561 = string;
export type SizeBytes = number;
/**
 * @maxItems 256
 */
export type Contradicting = ArtifactRef[];
export type CriterionId = string;
export type CriterionId1 = string;
export type NeedId = string;
export type Revision = number;
export type Reason =
  | "missing_answer"
  | "answer_contradicted"
  | "answer_unknown"
  | "no_matching_evidence"
  | "evidence_contradicted"
  | "evidence_conflict";
/**
 * @maxItems 256
 */
export type Supporting = ArtifactRef[];
/**
 * @minItems 1
 * @maxItems 4096
 */
export type Needs = AssessmentNeedDecision[];
export type Purpose = string;
export type CriterionId2 = string;
/**
 * @maxItems 32
 */
export type Answers = AssessmentAnswerRef[];
export type AssessmentId = string;
export type ProfileId = string;
export type Sha2562 = string;
export type Version1 = string;
export type QuestionId = string;
export type Revision1 = number;
/**
 * @maxItems 256
 */
export type Receipts = ArtifactRef[];
export type WireVersion = "1";
export type Reason1 =
  | "supporting"
  | "contradicting"
  | "unknown"
  | "scope_mismatch"
  | "need_revision_mismatch"
  | "criterion_mismatch"
  | "missing_answer"
  | "answer_revision_mismatch"
  | "method_mismatch"
  | "context_mismatch"
  | "category_mismatch"
  | "untrusted_issuer"
  | "purpose_mismatch"
  | "authority_mismatch";
/**
 * @maxItems 256
 */
export type Reviews = AssessmentReceiptReview[];
export type ScientificallyEstablished = false;
export type Sufficient = boolean;
export type WireVersion1 = "1";
export type Status2 = "assessed";
export type WireVersion2 = "1";

export interface EvidenceAssessmentStatus {
  actor_id: ActorId;
  outcome: Outcome;
  request: EvidenceAssessmentRequest;
  wire_version: WireVersion2;
}
export interface PendingAssessment {
  status: Status;
}
export interface FailedAssessment {
  code: Code;
  status: Status1;
}
export interface CompletedAssessment {
  assessment: EvidenceAssessment;
  status: Status2;
}
export interface EvidenceAssessment {
  actor_id: ActorId1;
  answered: Answered;
  authority: Authority;
  disposition: Disposition;
  needs: Needs;
  purpose: Purpose;
  request: EvidenceAssessmentRequest;
  reviews: Reviews;
  scientifically_established: ScientificallyEstablished;
  subject: ArtifactRef;
  sufficient: Sufficient;
  wire_version: WireVersion1;
}
export interface AssessmentNeedDecision {
  contradicting: Contradicting;
  criterion_id: CriterionId;
  gap: EvidenceGap | null;
  need: EvidenceNeedRef;
  supporting: Supporting;
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
export interface EvidenceGap {
  criterion_id: CriterionId1;
  need: EvidenceNeedRef;
  reason: Reason;
}
export interface EvidenceNeedRef {
  need_id: NeedId;
  revision: Revision;
  scope: Scope;
}
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
  criterion_id: CriterionId2;
}
export interface AssessmentProfileRef {
  profile_id: ProfileId;
  scope: Scope;
  sha256: Sha2562;
  version: Version1;
}
export interface ResearchQuestionRef {
  question_id: QuestionId;
  revision: Revision1;
  scope: Scope;
}
export interface AssessmentReceiptReview {
  reason: Reason1;
  receipt: ArtifactRef;
}
