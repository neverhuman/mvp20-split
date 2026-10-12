/* Generated from the published Python-owned serialization schema. Do not edit. */

export type RequestId = string;
export type ProjectId = string;
export type TenantId = string;
/**
 * @maxItems 16
 */
export type CapabilityRequests = CapabilityRequestRef[];
export type Authority = "proposal_only";
export type DecisionScope = string;
export type Outcome = CurationProposal | CurationCapabilityRequest | CurationAbstention;
export type Route = "next" | "true" | "false";
export type Source = string;
export type Target = string;
/**
 * @maxItems 1024
 */
export type Edges = ControlEdge[];
export type Name = string;
export type ValueType = ScalarType | ArtifactType | CollectionType;
export type Kind = "scalar";
export type Scalar = "boolean" | "integer" | "number" | "string";
export type Unit = string;
export type Kind1 = "artifact";
export type MediaType = string;
export type Representation = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Unit1 = string;
export type Item = ScalarType | ArtifactType;
export type Kind2 = "collection";
export type MaxItems = number;
export type MissingSlots = boolean;
/**
 * @maxItems 64
 */
export type Inputs = ValuePort[];
export type Checkpoint =
  | (
      | ScopeInput
      | NodeOutput
      | ScopeResult
      | BooleanConstant
      | IntegerConstant
      | NumberConstant
      | StringConstant
      | ArtifactConstant
    )
  | null;
export type Kind3 = "input";
export type Name1 = string;
export type Kind4 = "output";
export type NodeId = string;
export type Port = string;
export type Kind5 = "result";
export type Name2 = string;
export type Kind6 = "boolean";
export type Value = boolean;
export type Kind7 = "integer";
export type Unit2 = string;
export type Value1 = number;
export type Kind8 = "number";
export type Unit3 = string;
export type Value2 = number;
export type Kind9 = "string";
export type Value3 = string;
export type ArtifactId = string;
export type MediaType1 = string;
export type Sha2561 = string;
export type SizeBytes = number;
export type Kind10 = "artifact";
export type Representation1 = string;
export type Unit4 = string;
export type Port1 = string;
export type Source1 =
  | ScopeInput
  | NodeOutput
  | ScopeResult
  | BooleanConstant
  | IntegerConstant
  | NumberConstant
  | StringConstant
  | ArtifactConstant;
/**
 * @maxItems 64
 */
export type Inputs1 = ValueBinding[];
export type Kind11 = "invoke";
export type NodeId1 = string;
export type TimeoutSeconds = number;
export type CapabilityId = string;
export type ContractVersion = "1";
export type ImageSha256 = string;
export type Release = string;
export type Kind12 = "branch";
export type NodeId2 = string;
export type Predicate = ComparePredicate | ConstantPredicate | AllPredicate | AnyPredicate | NotPredicate;
export type Kind13 = "compare";
/**
 * @maxItems 16
 */
export type Path = (string | number)[];
export type Source2 =
  | ScopeInput
  | NodeOutput
  | ScopeResult
  | BooleanConstant
  | IntegerConstant
  | NumberConstant
  | StringConstant
  | ArtifactConstant;
export type Operator = "eq" | "ne" | "lt" | "le" | "gt" | "ge";
export type Right = BooleanConstant | IntegerConstant | NumberConstant | StringConstant;
export type Kind14 = "constant";
export type Value4 = boolean;
export type Kind15 = "all";
export type Kind16 = "any";
export type Kind17 = "not";
export type Predicate1 = ComparePredicate | ConstantPredicate | AllPredicate | AnyPredicate | NotPredicate;
/**
 * @minItems 1
 * @maxItems 16
 */
export type Predicates1 = (ComparePredicate | ConstantPredicate | AllPredicate | AnyPredicate | NotPredicate)[];
/**
 * @minItems 1
 * @maxItems 16
 */
export type Predicates = (ComparePredicate | ConstantPredicate | AllPredicate | AnyPredicate | NotPredicate)[];
export type Kind18 = "join";
export type MemberId = string;
export type Required = boolean;
export type Source3 =
  | ScopeInput
  | NodeOutput
  | ScopeResult
  | BooleanConstant
  | IntegerConstant
  | NumberConstant
  | StringConstant
  | ArtifactConstant;
/**
 * @maxItems 10000
 */
export type Members = JoinMember[];
export type NodeId3 = string;
export type Policy = AllCollectionPolicy | PartialCollectionPolicy;
export type Kind19 = "all";
export type Skipped = "exclude" | "fail";
export type Close = "all_terminal" | "deadline";
export type DeadlineSeconds = number | null;
export type Kind20 = "partial";
export type Minimum = number;
/**
 * @maxItems 64
 */
export type Captures = ValueBinding[];
export type Collection =
  | ScopeInput
  | NodeOutput
  | ScopeResult
  | BooleanConstant
  | IntegerConstant
  | NumberConstant
  | StringConstant
  | ArtifactConstant;
export type ItemInput = string;
export type Kind21 = "scatter";
export type MaxMembers = number;
export type MaxParallel = number;
export type NodeId4 = string;
export type Policy1 = AllCollectionPolicy | PartialCollectionPolicy;
export type ResultPort = string;
/**
 * @maxItems 64
 */
export type Captures1 = ValueBinding[];
export type Kind22 = "iterate";
export type MaxIterations = number;
export type NodeId5 = string;
export type OnLimit = "finish" | "blocked";
export type FeedbackPort = string;
export type Initial =
  | ScopeInput
  | NodeOutput
  | ScopeResult
  | BooleanConstant
  | IntegerConstant
  | NumberConstant
  | StringConstant
  | ArtifactConstant;
export type Name3 = string;
export type ValueType1 = ScalarType | ArtifactType | CollectionType;
/**
 * @minItems 1
 * @maxItems 64
 */
export type State = LoopStateSlot[];
export type Until = ComparePredicate | ConstantPredicate | AllPredicate | AnyPredicate | NotPredicate;
export type Kind23 = "finish";
export type NodeId6 = string;
/**
 * @maxItems 64
 */
export type Outputs = ValueBinding[];
export type ExpectedRevision = string;
export type IssuerId = string;
export type Kind24 = "await";
export type NodeId7 = string;
export type OnTimeout = "blocked" | "abstained";
export type Purpose = string;
export type Subject =
  | ScopeInput
  | NodeOutput
  | ScopeResult
  | BooleanConstant
  | IntegerConstant
  | NumberConstant
  | StringConstant
  | ArtifactConstant;
export type TimeoutSeconds1 = number;
export type Kind25 = "artifact_project";
export type MaxArtifacts = number;
export type MaxBytes = number;
export type MaxItems1 = number;
export type TimeoutSeconds2 = number;
export type Mode = "values" | "references" | "items";
export type NodeId8 = string;
/**
 * @maxItems 16
 */
export type Path1 = (string | number)[];
export type Source4 =
  | ScopeInput
  | NodeOutput
  | ScopeResult
  | BooleanConstant
  | IntegerConstant
  | NumberConstant
  | StringConstant
  | ArtifactConstant;
export type Mode1 = "inline" | "references";
export type Name4 = string;
export type Source5 =
  | ScopeInput
  | NodeOutput
  | ScopeResult
  | BooleanConstant
  | IntegerConstant
  | NumberConstant
  | StringConstant
  | ArtifactConstant;
/**
 * @maxItems 64
 */
export type Fields = MaterializeField[];
export type Kind26 = "artifact_materialize";
export type NodeId9 = string;
/**
 * @minItems 1
 * @maxItems 256
 */
export type Nodes = (
  InvokeV2 | BranchV2 | JoinV2 | ScatterV4 | IterateV4 | FinishV2 | AwaitV3 | ArtifactProjectV4 | ArtifactMaterializeV4
)[];
/**
 * @maxItems 64
 */
export type Outputs1 = ValuePort[];
export type CampaignId = string;
export type Identity = string;
export type Kind27 = "policy" | "evaluator" | "model" | "source" | "knowledge";
export type Revision = string;
export type Sha2562 = string;
/**
 * @maxItems 256
 */
export type Context = ContextPin[];
export type Profile = "deterministic-v3";
export type Revision1 = number;
export type SchemaVersion = "4";
export type CriterionId = string;
/**
 * @maxItems 32
 */
export type Answers = AssessmentAnswerRef[];
export type AssessmentId = string;
export type ProfileId = string;
export type Sha2563 = string;
export type Version1 = string;
export type QuestionId = string;
export type Revision2 = number;
/**
 * @maxItems 256
 */
export type Receipts = ArtifactRef[];
export type WireVersion = "1";
export type StatusSha256 = string;
/**
 * @maxItems 16
 */
export type Assessments = CampaignAssessmentSelection[];
export type ExpectedEvidence1 = string;
export type NeedId = string;
export type Revision3 = number;
/**
 * @maxItems 16
 */
export type Needs = EvidenceNeedRef[];
export type NodeId10 = string;
/**
 * @maxItems 16
 */
export type ScopePath = string[];
export type Uncertainty = string;
/**
 * @maxItems 64
 */
export type ExpectedEvidence = CampaignEvidenceIntent[];
export type Kind28 = "future_campaign";
export type Title = string;
/**
 * @minItems 1
 * @maxItems 16
 */
export type AcceptanceCriteria = string[];
/**
 * @minItems 1
 * @maxItems 16
 */
export type Applicability = string[];
export type EvidenceNeed = string;
export type GapKey = string;
export type GraphGap = string;
export type Description = string;
export type Name5 = string;
export type Representation2 = string;
export type Unit5 = string | null;
/**
 * @maxItems 32
 */
export type Inputs2 = RequestedCapabilityPort[];
/**
 * @minItems 1
 * @maxItems 32
 */
export type Outputs2 = RequestedCapabilityPort[];
export type Purpose1 = string;
/**
 * @maxItems 16
 */
export type Gaps = CapabilityGap[];
export type Kind29 = "propose_campaign";
/**
 * @minItems 1
 * @maxItems 16
 */
export type Gaps1 = CapabilityGap[];
export type Kind30 = "request_capabilities";
export type Kind31 = "abstain";
export type ReasonCode = string;
export type Profile1 = "planning.campaign-curation-draft.v1";
export type Rationale = string;
export type SchemaVersion1 = "1";
export type ScientificAuthority = "not_established";
export type Description1 = string;
export type Posture = "unknown" | "weak" | "contradictory" | "missing" | "inapplicable";
/**
 * @maxItems 64
 */
export type Unresolved = CampaignUnresolvedPoint[];
export type EngagementId = string;
export type Ordinal = number;
export type RequestSha256 = string;
export type EnvelopeSha256 = string;
export type OutputSha256 = string | null;
export type ReservationUnits = number;
export type AccountingUnits = number | null;
export type Certainty = "reported" | "unknown";
export type InputTokens = number | null;
export type OutputTokens = number | null;
export type CreatedAt = string;
export type ActorId = string;
export type CommandFamily = string;
export type CommandId = string;
export type SchemaVersion2 = "1";
export type Phase =
  | "queued"
  | "assembling"
  | "awaiting_provider"
  | "proposed"
  | "abstained"
  | "compiling"
  | "ready"
  | "failed"
  | "indeterminate";
export type ReasonCode1 = string | null;
export type CurationId = string;
export type RequestSha2561 = string;
export type Revision4 = number;
export type UpdatedAt = string;
export type WireVersion1 = "1";
/**
 * @maxItems 16
 */
export type Artifacts = ArtifactRef[];
export type ContentSha256 = string;
export type DraftId = string;
export type Revision5 = number;
export type ChangeId = string;
export type GraphId = string;
export type Position = number;
export type Sha2564 = string;
export type Revision6 = number;
export type Sha2565 = string;
/**
 * @maxItems 8
 */
export type Knowledge = DomainHead[];
/**
 * @maxItems 32
 */
export type Needs1 = EvidenceNeedRef[];
export type PlanSha256 = string;
export type Revision7 = number;
export type RunId = string;
/**
 * @maxItems 32
 */
export type Questions = ResearchQuestionRef[];
export type Direction = string;
export type PolicyId = string;
export type ContentSha2561 = string;
export type DraftId1 = string;
export type Revision8 = number;
export type UniverseSha256 = string;
export type ValidationId = string;
export type WireVersion2 = "1";

export interface CurationView {
  capability_requests: CapabilityRequests;
  proposal: CampaignCurationDraft | null;
  provider: CurationProviderRecord | null;
  receipt: CurationReceipt;
  specification: CurationSpecification;
  validated_draft: DraftSelection | null;
  wire_version?: WireVersion2;
}
export interface CapabilityRequestRef {
  request_id: RequestId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface CampaignCurationDraft {
  authority: Authority;
  decision_scope: DecisionScope;
  outcome: Outcome;
  profile: Profile1;
  rationale: Rationale;
  schema_version?: SchemaVersion1;
  scientific_authority: ScientificAuthority;
  unresolved: Unresolved;
}
export interface CurationProposal {
  candidate: FutureCampaignDraft;
  gaps: Gaps;
  kind: Kind29;
}
export interface FutureCampaignDraft {
  definition: ExecutableCampaignV4;
  expected_evidence: ExpectedEvidence;
  kind: Kind28;
  title: Title;
}
export interface ExecutableCampaignV4 {
  body: ExecutableScopeV4;
  campaign_id: CampaignId;
  context?: Context;
  profile: Profile;
  revision: Revision1;
  schema_version: SchemaVersion;
  scope: Scope;
}
export interface ExecutableScopeV4 {
  edges?: Edges;
  inputs?: Inputs;
  nodes: Nodes;
  outputs?: Outputs1;
}
export interface ControlEdge {
  route?: Route;
  source: Source;
  target: Target;
}
export interface ValuePort {
  name: Name;
  value_type: ValueType;
}
export interface ScalarType {
  kind: Kind;
  scalar: Scalar;
  unit?: Unit;
}
export interface ArtifactType {
  kind: Kind1;
  media_type?: MediaType;
  representation: Representation;
  schema_ref: SchemaRef;
  unit: Unit1;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha256;
  version: Version;
}
export interface CollectionType {
  item: Item;
  kind: Kind2;
  max_items: MaxItems;
  missing_slots?: MissingSlots;
}
export interface InvokeV2 {
  checkpoint?: Checkpoint;
  inputs: Inputs1;
  kind: Kind11;
  node_id: NodeId1;
  timeout_seconds: TimeoutSeconds;
  tool: ToolBinding;
}
export interface ScopeInput {
  kind: Kind3;
  name: Name1;
}
export interface NodeOutput {
  kind: Kind4;
  node_id: NodeId;
  port: Port;
}
export interface ScopeResult {
  kind: Kind5;
  name: Name2;
}
export interface BooleanConstant {
  kind: Kind6;
  value: Value;
}
export interface IntegerConstant {
  kind: Kind7;
  unit?: Unit2;
  value: Value1;
}
export interface NumberConstant {
  kind: Kind8;
  unit?: Unit3;
  value: Value2;
}
export interface StringConstant {
  kind: Kind9;
  value: Value3;
}
export interface ArtifactConstant {
  artifact: ArtifactRef;
  kind: Kind10;
  representation: Representation1;
  unit: Unit4;
}
export interface ArtifactRef {
  artifact_id: ArtifactId;
  media_type: MediaType1;
  schema_ref: SchemaRef;
  scope: Scope;
  sha256: Sha2561;
  size_bytes: SizeBytes;
}
export interface ValueBinding {
  port: Port1;
  source: Source1;
}
export interface ToolBinding {
  capability_id: CapabilityId;
  contract_version: ContractVersion;
  image_sha256: ImageSha256;
  release: Release;
}
export interface BranchV2 {
  kind: Kind12;
  node_id: NodeId2;
  predicate: Predicate;
}
export interface ComparePredicate {
  kind: Kind13;
  left: ScalarProjection;
  operator: Operator;
  right: Right;
}
export interface ScalarProjection {
  path?: Path;
  source: Source2;
  value_type: ScalarType;
}
export interface ConstantPredicate {
  kind: Kind14;
  value: Value4;
}
export interface AllPredicate {
  kind: Kind15;
  predicates: Predicates;
}
export interface AnyPredicate {
  kind: Kind16;
  predicates: Predicates1;
}
export interface NotPredicate {
  kind: Kind17;
  predicate: Predicate1;
}
export interface JoinV2 {
  kind: Kind18;
  members: Members;
  node_id: NodeId3;
  output: ValuePort;
  policy: Policy;
}
export interface JoinMember {
  member_id: MemberId;
  required?: Required;
  source: Source3;
}
export interface AllCollectionPolicy {
  kind: Kind19;
  skipped?: Skipped;
}
export interface PartialCollectionPolicy {
  close: Close;
  deadline_seconds?: DeadlineSeconds;
  kind: Kind20;
  minimum: Minimum;
}
export interface ScatterV4 {
  body: ExecutableScopeV4;
  captures?: Captures;
  collection: Collection;
  item_input: ItemInput;
  kind: Kind21;
  max_members: MaxMembers;
  max_parallel: MaxParallel;
  node_id: NodeId4;
  output: ValuePort;
  policy: Policy1;
  result_port: ResultPort;
}
export interface IterateV4 {
  body: ExecutableScopeV4;
  captures?: Captures1;
  kind: Kind22;
  max_iterations: MaxIterations;
  node_id: NodeId5;
  on_limit: OnLimit;
  state: State;
  until: Until;
}
export interface LoopStateSlot {
  feedback_port: FeedbackPort;
  initial: Initial;
  name: Name3;
  value_type: ValueType1;
}
export interface FinishV2 {
  kind: Kind23;
  node_id: NodeId6;
  outputs: Outputs;
}
export interface AwaitV3 {
  expected_revision: ExpectedRevision;
  issuer_id: IssuerId;
  kind: Kind24;
  node_id: NodeId7;
  on_timeout: OnTimeout;
  output: ValuePort;
  purpose: Purpose;
  subject: Subject;
  timeout_seconds: TimeoutSeconds1;
}
export interface ArtifactProjectV4 {
  kind: Kind25;
  limits?: BindingLimits;
  mode: Mode;
  node_id: NodeId8;
  output: ValuePort;
  path?: Path1;
  source: Source4;
}
export interface BindingLimits {
  max_artifacts?: MaxArtifacts;
  max_bytes?: MaxBytes;
  max_items?: MaxItems1;
  timeout_seconds?: TimeoutSeconds2;
}
export interface ArtifactMaterializeV4 {
  fields: Fields;
  kind: Kind26;
  limits?: BindingLimits;
  node_id: NodeId9;
  output: ValuePort;
}
export interface MaterializeField {
  mode: Mode1;
  name: Name4;
  source: Source5;
}
export interface ContextPin {
  identity: Identity;
  kind: Kind27;
  revision: Revision;
  sha256: Sha2562;
}
export interface CampaignEvidenceIntent {
  assessments: Assessments;
  expected_evidence: ExpectedEvidence1;
  needs: Needs;
  producer: CampaignNodeAddress | null;
  question: ResearchQuestionRef;
  uncertainty: Uncertainty;
}
export interface CampaignAssessmentSelection {
  request: EvidenceAssessmentRequest;
  status_sha256: StatusSha256;
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
  sha256: Sha2563;
  version: Version1;
}
export interface ResearchQuestionRef {
  question_id: QuestionId;
  revision: Revision2;
  scope: Scope;
}
export interface EvidenceNeedRef {
  need_id: NeedId;
  revision: Revision3;
  scope: Scope;
}
export interface CampaignNodeAddress {
  node_id: NodeId10;
  scope_path: ScopePath;
}
/**
 * Model-local key; durable request identity is assigned by Planning.
 */
export interface CapabilityGap {
  acceptance_criteria: AcceptanceCriteria;
  applicability: Applicability;
  evidence_need: EvidenceNeed;
  gap_key: GapKey;
  graph_gap: GraphGap;
  inputs: Inputs2;
  outputs: Outputs2;
  purpose: Purpose1;
}
export interface RequestedCapabilityPort {
  description: Description;
  name: Name5;
  representation: Representation2;
  schema_ref: SchemaRef | null;
  unit: Unit5;
}
export interface CurationCapabilityRequest {
  gaps: Gaps1;
  kind: Kind30;
}
export interface CurationAbstention {
  kind: Kind31;
  reason_code: ReasonCode;
}
export interface CampaignUnresolvedPoint {
  description: Description1;
  need: EvidenceNeedRef | null;
  posture: Posture;
  question: ResearchQuestionRef | null;
}
export interface CurationProviderRecord {
  attempt: ProviderAttemptRef;
  envelope_sha256: EnvelopeSha256;
  output_sha256: OutputSha256;
  reservation_units: ReservationUnits;
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
export interface ProviderUsage {
  accounting_units: AccountingUnits;
  certainty: Certainty;
  input_tokens: InputTokens;
  output_tokens: OutputTokens;
}
export interface CurationReceipt {
  created_at: CreatedAt;
  identity: CommandIdentity;
  phase: Phase;
  reason_code: ReasonCode1;
  reference: CurationRef;
  request_sha256: RequestSha2561;
  revision: Revision4;
  updated_at: UpdatedAt;
  wire_version?: WireVersion1;
}
export interface CommandIdentity {
  actor_id: ActorId;
  command_family: CommandFamily;
  command_id: CommandId;
  schema_version?: SchemaVersion2;
  scope: Scope;
}
export interface CurationRef {
  curation_id: CurationId;
  scope: Scope;
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
  needs: Needs1;
  predecessor: PredecessorCut;
  questions: Questions;
}
export interface CampaignOriginDraft {
  content_sha256: ContentSha256;
  draft_id: DraftId;
  revision: Revision5;
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
  sha256: Sha2564;
}
export interface DomainGraphRef {
  graph_id: GraphId;
  scope: Scope;
}
export interface DomainRevisionRef {
  graph: DomainGraphRef;
  revision: Revision6;
  sha256: Sha2565;
}
export interface PredecessorCut {
  plan_sha256: PlanSha256;
  revision: Revision7;
  run_id: RunId;
}
export interface DraftSelection {
  content_sha256: ContentSha2561;
  draft_id: DraftId1;
  revision: Revision8;
  universe_sha256: UniverseSha256;
  validation_id: ValidationId;
}
