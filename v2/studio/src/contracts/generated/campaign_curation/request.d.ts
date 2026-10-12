/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Encoding = "amphora-command-v2";
export type ActorId = string;
export type CommandFamily = string;
export type CommandId = string;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Sha2561 = string;
export type SizeBytes = number;
/**
 * @maxItems 16
 */
export type Artifacts = ArtifactRef[];
export type ContentSha256 = string;
export type DraftId = string;
export type Revision = number;
export type ChangeId = string;
export type GraphId = string;
export type Position = number;
export type Sha2562 = string;
export type Revision1 = number;
export type Sha2563 = string;
/**
 * @maxItems 8
 */
export type Knowledge = DomainHead[];
export type NeedId = string;
export type Revision2 = number;
/**
 * @maxItems 32
 */
export type Needs = EvidenceNeedRef[];
export type PlanSha256 = string;
export type Revision3 = number;
export type RunId = string;
export type QuestionId = string;
export type Revision4 = number;
/**
 * @maxItems 32
 */
export type Questions = ResearchQuestionRef[];
export type Direction = string;
export type PolicyId = string;

export interface CurationRequest {
  encoding: Encoding;
  identity: CommandIdentity;
  payload: CurationSpecification;
}
export interface CommandIdentity {
  actor_id: ActorId;
  command_family: CommandFamily;
  command_id: CommandId;
  schema_version?: SchemaVersion;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface CurationSpecification {
  context: CurationContext;
  direction: Direction;
  policy_id: PolicyId;
}
export interface CurationContext {
  artifacts: Artifacts;
  draft: CampaignOriginDraft;
  knowledge: Knowledge;
  needs: Needs;
  predecessor: PredecessorCut;
  questions: Questions;
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
export interface CampaignOriginDraft {
  content_sha256: ContentSha256;
  draft_id: DraftId;
  revision: Revision;
  scope: Scope;
}
export interface DomainHead {
  change: AcceptedChangeRef;
  snapshot: DomainRevisionRef;
}
export interface AcceptedChangeRef {
  change_id: ChangeId;
  graph: DomainGraphRef;
  position: Position;
  sha256: Sha2562;
}
export interface DomainGraphRef {
  graph_id: GraphId;
  scope: Scope;
}
export interface DomainRevisionRef {
  graph: DomainGraphRef;
  revision: Revision1;
  sha256: Sha2563;
}
export interface EvidenceNeedRef {
  need_id: NeedId;
  revision: Revision2;
  scope: Scope;
}
export interface PredecessorCut {
  plan_sha256: PlanSha256;
  revision: Revision3;
  run_id: RunId;
}
export interface ResearchQuestionRef {
  question_id: QuestionId;
  revision: Revision4;
  scope: Scope;
}
