/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Authority = "historical_compiler_provenance";
export type ContentSha256 = string;
export type DraftId = string;
export type Revision = number;
export type ProjectId = string;
export type TenantId = string;
export type AssertionId = string;
export type GraphId = string;
export type Revision1 = number;
/**
 * @maxItems 256
 */
export type Assertions = AssertionRevisionRef[];
export type ContextSha256 = string | null;
export type EntityId = string;
export type Revision2 = number;
/**
 * @maxItems 256
 */
export type Entities = EntityRevisionRef[];
export type ChangeId = string;
export type Position = number;
export type Sha256 = string;
export type Revision3 = number;
export type Sha2561 = string;
export type PolicyId = string;
export type Sha2562 = string;
export type Version = string;
export type SelectionSha256 = string;
export type Status = "available" | "unavailable";
export type Unavailable = string | null;
export type Sha2563 = string;
export type Version1 = string;
export type VocabularyId = string;
/**
 * @minItems 1
 * @maxItems 16
 */
export type Limitations = string[];
export type Action = "propose_campaign";
export type ActorId = string;
export type EngagementId = string;
export type Ordinal = number;
export type RequestSha256 = string;
export type CapturePublication = "not_published";
/**
 * @minItems 1
 * @maxItems 4
 */
export type AllowedActions = ("abstain" | "request_evidence" | "propose_knowledge_change" | "propose_campaign")[];
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha2564 = string;
export type Version2 = "1";
export type Sha2565 = string;
export type SizeBytes = number;
export type Required = boolean;
export type Role = "constraint" | "source" | "capability" | "knowledge" | "result";
/**
 * @maxItems 128
 */
export type Entries = ContextEntry[];
export type AccountingUnit = string;
export type MaxAttempts = number;
export type MaxInputTokens = number;
export type MaxOutputTokens = number;
export type TotalAccountingUnits = number;
export type TotalTokens = number;
export type ContextWindowTokens = number;
export type ModelId = string;
export type ModelRevision = string;
export type ProviderId = string;
export type Reason = "budget" | "not_relevant" | "unavailable" | "not_authorized";
/**
 * @maxItems 128
 */
export type Omissions = ContextOmission[];
export type SchemaVersion = "1";
export type OutputSha256 = string;
export type PreparationSha256 = string;
export type PreparedProposalSha256 = string;
export type Rationale = string;
export type AccountingUnits = number | null;
export type Certainty = "reported" | "unknown";
export type InputTokens = number | null;
export type OutputTokens = number | null;
/**
 * @maxItems 32
 */
export type CriterionIds = string[];
export type Kind = "question" | "need" | "assessment";
export type RecordSha256 = string | null;
export type Reference = ResearchQuestionRef | EvidenceNeedRef | EvidenceAssessmentRequest;
export type QuestionId = string;
export type Revision4 = number;
export type NeedId = string;
export type Revision5 = number;
export type CriterionId = string;
/**
 * @maxItems 32
 */
export type Answers = AssessmentAnswerRef[];
export type AssessmentId = string;
export type ProfileId = string;
export type Sha2566 = string;
export type Version3 = string;
/**
 * @maxItems 256
 */
export type Receipts = ArtifactRef[];
export type WireVersion = "1";
export type Unavailable1 = ("not_provided" | "unavailable" | "denied" | "pending" | "failed") | null;
/**
 * @maxItems 160
 */
export type Records = CampaignOriginResearchRecord[];
export type Selection = (CampaignResearchSelection | CampaignFollowupSelection) | null;
export type StatusSha256 = string;
/**
 * @maxItems 32
 */
export type Assessments = CampaignAssessmentSelection[];
/**
 * @maxItems 64
 */
export type Needs = EvidenceNeedRef[];
/**
 * @maxItems 64
 */
export type Questions = ResearchQuestionRef[];
export type RequestSha2561 = string;
export type SchemaVersion1 = "1";
/**
 * @maxItems 32
 */
export type Assessments1 = CampaignAssessmentSelection[];
export type CriterionId1 = string;
/**
 * @maxItems 64
 */
export type Criteria = CampaignCriterionRef[];
/**
 * @maxItems 64
 */
export type Needs1 = EvidenceNeedRef[];
/**
 * @maxItems 64
 */
export type Questions1 = ResearchQuestionRef[];
export type RequestSha2562 = string;
export type SchemaVersion2 = "2";
export type EffectId = string;
export type EffectSha256 = string;
export type OwnerId = string;
export type ReadbackSha256 = string;
export type Outcome = DraftAccepted | DraftRejected | DraftPending;
export type ActorId1 = string;
export type CommandFamily = string;
export type CommandId = string;
export type SchemaVersion3 = "1";
export type OperationId = string;
export type RequestSha2563 = string;
export type ContentSha2561 = string;
export type Kind1 = "draft_revision" | "draft_validation";
export type ObjectId = string;
export type Revision6 = number;
export type Status1 = "accepted";
export type ReasonCode = string;
export type Status2 = "rejected";
export type Status3 = "pending";
export type SchemaVersion4 = "1";
export type SelectionId = string;
export type SelectionSha2561 = string;
export type SchemaVersion5 = "2";
export type NodeId = string;
/**
 * @maxItems 16
 */
export type ScopePath = string[];
export type DescriptorSha256 = string;
export type Port = string;
/**
 * @maxItems 64
 */
export type InputSchemas = PortSchemaLock[];
/**
 * @maxItems 64
 */
export type OutputSchemas = PortSchemaLock[];
export type SchemaVersion6 = "1";
export type CapabilityId = string;
export type ContractVersion = "1";
export type ImageSha256 = string;
export type Release = string;
/**
 * @maxItems 4096
 */
export type Tools = CampaignOriginTool[];
export type OriginSha256 = string;
export type SchemaVersion7 = "2";

export interface CampaignOriginV2 {
  origin: CampaignOriginBodyV2;
  origin_sha256: OriginSha256;
  schema_version?: SchemaVersion7;
}
export interface CampaignOriginBodyV2 {
  authority: Authority;
  draft: CampaignOriginDraft;
  knowledge: CampaignOriginKnowledge | null;
  limitations: Limitations;
  proposal: CampaignOriginProposal;
  research: CampaignOriginResearch;
  save: CampaignOriginSave;
  schema_version?: SchemaVersion5;
  tools: Tools;
}
export interface CampaignOriginDraft {
  content_sha256: ContentSha256;
  draft_id: DraftId;
  revision: Revision;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface CampaignOriginKnowledge {
  assertions: Assertions;
  context_sha256: ContextSha256;
  entities: Entities;
  graph: DomainGraphRef;
  head: DomainHead | null;
  policy: StructuralPolicyRef | null;
  selection_sha256: SelectionSha256;
  status: Status;
  unavailable: Unavailable;
  vocabulary: VocabularyRef | null;
}
export interface AssertionRevisionRef {
  assertion_id: AssertionId;
  graph: DomainGraphRef;
  revision: Revision1;
}
export interface DomainGraphRef {
  graph_id: GraphId;
  scope: Scope;
}
export interface EntityRevisionRef {
  entity_id: EntityId;
  graph: DomainGraphRef;
  revision: Revision2;
}
export interface DomainHead {
  change: AcceptedChangeRef;
  snapshot: DomainRevisionRef;
}
export interface AcceptedChangeRef {
  change_id: ChangeId;
  graph: DomainGraphRef;
  position: Position;
  sha256: Sha256;
}
export interface DomainRevisionRef {
  graph: DomainGraphRef;
  revision: Revision3;
  sha256: Sha2561;
}
export interface StructuralPolicyRef {
  policy_id: PolicyId;
  sha256: Sha2562;
  version: Version;
}
export interface VocabularyRef {
  sha256: Sha2563;
  version: Version1;
  vocabulary_id: VocabularyId;
}
export interface CampaignOriginProposal {
  action: Action;
  actor_id: ActorId;
  attempt: ProviderAttemptRef;
  capture_publication: CapturePublication;
  context: ContextManifest;
  output_sha256: OutputSha256;
  preparation_sha256: PreparationSha256;
  prepared_proposal_sha256: PreparedProposalSha256;
  rationale: Rationale;
  usage: ProviderUsage;
}
export interface ProviderAttemptRef {
  engagement: EngagementRef;
  ordinal: Ordinal;
  request_sha256: RequestSha256;
}
export interface EngagementRef {
  engagement_id: EngagementId;
  scope: Scope;
}
export interface ContextManifest {
  allowed_actions: AllowedActions;
  entries: Entries;
  limits: CallLimits;
  model: ModelBinding;
  objective: ArtifactRef;
  omissions: Omissions;
  output_schema: SchemaRef;
  policy: ArtifactRef;
  prompt: ArtifactRef;
  schema_version?: SchemaVersion;
  scope: Scope;
}
export interface ContextEntry {
  artifact: ArtifactRef;
  required: Required;
  role: Role;
}
export interface ArtifactRef {
  artifact_id: ArtifactId;
  media_type: MediaType;
  schema_ref: SchemaRef;
  scope: Scope;
  sha256: Sha2565;
  size_bytes: SizeBytes;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha2564;
  version: Version2;
}
export interface CallLimits {
  accounting_unit: AccountingUnit;
  max_attempts: MaxAttempts;
  max_input_tokens: MaxInputTokens;
  max_output_tokens: MaxOutputTokens;
  total_accounting_units: TotalAccountingUnits;
  total_tokens: TotalTokens;
}
export interface ModelBinding {
  configuration: ArtifactRef;
  context_window_tokens: ContextWindowTokens;
  model_id: ModelId;
  model_revision: ModelRevision;
  provider_id: ProviderId;
  tokenizer: SchemaRef;
}
export interface ContextOmission {
  artifact: ArtifactRef;
  reason: Reason;
}
export interface ProviderUsage {
  accounting_units: AccountingUnits;
  certainty: Certainty;
  input_tokens: InputTokens;
  output_tokens: OutputTokens;
}
export interface CampaignOriginResearch {
  records: Records;
  selection: Selection;
}
export interface CampaignOriginResearchRecord {
  criterion_ids: CriterionIds;
  kind: Kind;
  record_sha256: RecordSha256;
  reference: Reference;
  unavailable: Unavailable1;
}
export interface ResearchQuestionRef {
  question_id: QuestionId;
  revision: Revision4;
  scope: Scope;
}
export interface EvidenceNeedRef {
  need_id: NeedId;
  revision: Revision5;
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
  criterion_id: CriterionId;
}
export interface AssessmentProfileRef {
  profile_id: ProfileId;
  scope: Scope;
  sha256: Sha2566;
  version: Version3;
}
export interface CampaignResearchSelection {
  assessments: Assessments;
  engagement: EngagementRef;
  needs: Needs;
  questions: Questions;
  request_sha256: RequestSha2561;
  schema_version?: SchemaVersion1;
}
export interface CampaignAssessmentSelection {
  request: EvidenceAssessmentRequest;
  status_sha256: StatusSha256;
}
export interface CampaignFollowupSelection {
  assessments: Assessments1;
  criteria: Criteria;
  engagement: EngagementRef;
  focus_artifact: ArtifactRef | null;
  needs: Needs1;
  questions: Questions1;
  request_sha256: RequestSha2562;
  schema_version?: SchemaVersion2;
}
export interface CampaignCriterionRef {
  assessment: CampaignAssessmentSelection | null;
  criterion_id: CriterionId1;
  need: EvidenceNeedRef;
  question: ResearchQuestionRef;
}
export interface CampaignOriginSave {
  effect_id: EffectId;
  effect_sha256: EffectSha256;
  owner_id: OwnerId;
  readback_sha256: ReadbackSha256;
  receipt: DraftCommandReceipt;
  selection_id: SelectionId;
  selection_sha256: SelectionSha2561;
}
export interface DraftCommandReceipt {
  outcome: Outcome;
  schema_version?: SchemaVersion4;
}
export interface DraftAccepted {
  binding: DraftReceiptBinding;
  committed: DraftCommit;
  status: Status1;
}
export interface DraftReceiptBinding {
  identity: CommandIdentity;
  operation_id: OperationId;
  request_sha256: RequestSha2563;
}
export interface CommandIdentity {
  actor_id: ActorId1;
  command_family: CommandFamily;
  command_id: CommandId;
  schema_version?: SchemaVersion3;
  scope: Scope;
}
export interface DraftCommit {
  content_sha256: ContentSha2561;
  kind: Kind1;
  object_id: ObjectId;
  revision: Revision6;
}
export interface DraftRejected {
  binding: DraftReceiptBinding;
  reason_code: ReasonCode;
  status: Status2;
}
export interface DraftPending {
  binding: DraftReceiptBinding;
  status: Status3;
}
export interface CampaignOriginTool {
  node: CampaignNodeAddress;
  release: LockEntry;
}
export interface CampaignNodeAddress {
  node_id: NodeId;
  scope_path: ScopePath;
}
export interface LockEntry {
  checkpoint_schema: SchemaRef | null;
  descriptor_sha256: DescriptorSha256;
  input_schemas: InputSchemas;
  output_schemas: OutputSchemas;
  schema_version?: SchemaVersion6;
  tool: ToolBinding;
}
export interface PortSchemaLock {
  port: Port;
  schema_ref: SchemaRef;
}
export interface ToolBinding {
  capability_id: CapabilityId;
  contract_version: ContractVersion;
  image_sha256: ImageSha256;
  release: Release;
}
