/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Action = "abstain" | "request_evidence" | "propose_campaign";
export type CandidateId = string;
export type Description = string;
export type DescriptorSha256 = string | null;
export type Reason = string;
/**
 * @maxItems 16
 */
export type Alternatives = CampaignAlternative[];
export type Authority = "proposal_only";
export type Candidate = (FutureCampaignDraft | MaterializationAdjustmentDraft) | null;
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
export type ProjectId = string;
export type TenantId = string;
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
export type FieldName = string;
export type PreviousValueSha256 = string;
export type Proposed = BooleanConstant | IntegerConstant | NumberValue | StringConstant;
export type Kind29 = "number";
export type Unit5 = string;
export type Value5 = string;
export type NodeId11 = string;
export type Index = number;
export type Kind30 = "loop";
export type NodeId12 = string;
export type Index1 = number;
export type Kind31 = "scatter";
export type MembershipSha256 = string;
export type NodeId13 = string;
/**
 * @maxItems 16
 */
export type Occurrences = (LoopOccurrence | ScatterOccurrence)[];
export type SchemaVersion1 = "2";
/**
 * @minItems 1
 * @maxItems 64
 */
export type Changes = MaterializationFieldProposal[];
export type CheckpointSeedSha256 = string;
export type FrontierRevision = number;
export type PlanSha256 = string;
export type Revision4 = number;
export type RunId = string;
/**
 * @maxItems 64
 */
export type ExpectedEvidence2 = CampaignEvidenceIntent[];
export type Kind32 = "materialization_adjustment";
export type DecisionScope = string;
/**
 * @maxItems 64
 */
export type EvidenceRequests = CampaignEvidenceIntent[];
export type Rationale = string;
export type SchemaVersion2 = "2";
export type ScientificAuthority = "not_established";
export type Description1 = string;
export type Posture = "unknown" | "weak" | "contradictory" | "missing" | "inapplicable";
/**
 * @maxItems 64
 */
export type Unresolved = CampaignUnresolvedPoint[];

export interface CheckpointDraft {
  action: Action;
  alternatives: Alternatives;
  authority: Authority;
  candidate: Candidate;
  decision_scope: DecisionScope;
  evidence_requests: EvidenceRequests;
  rationale: Rationale;
  schema_version?: SchemaVersion2;
  scientific_authority: ScientificAuthority;
  unresolved: Unresolved;
}
export interface CampaignAlternative {
  candidate_id: CandidateId;
  description: Description;
  descriptor_sha256: DescriptorSha256;
  reason: Reason;
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
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
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
export interface MaterializationAdjustmentDraft {
  changes: Changes;
  checkpoint_seed_sha256: CheckpointSeedSha256;
  cut: GraphReadCut;
  expected_evidence: ExpectedEvidence2;
  kind: Kind32;
}
export interface MaterializationFieldProposal {
  field_name: FieldName;
  previous_value_sha256: PreviousValueSha256;
  proposed: Proposed;
  target: ActivationPath;
}
export interface NumberValue {
  kind: Kind29;
  unit?: Unit5;
  value: Value5;
}
export interface ActivationPath {
  node_id: NodeId11;
  occurrences?: Occurrences;
  schema_version: SchemaVersion1;
}
export interface LoopOccurrence {
  index: Index;
  kind: Kind30;
  node_id: NodeId12;
}
export interface ScatterOccurrence {
  index: Index1;
  kind: Kind31;
  membership_sha256: MembershipSha256;
  node_id: NodeId13;
}
export interface GraphReadCut {
  frontier_revision: FrontierRevision;
  plan_sha256: PlanSha256;
  revision: Revision4;
  run_id: RunId;
  scope: Scope;
}
export interface CampaignUnresolvedPoint {
  description: Description1;
  need: EvidenceNeedRef | null;
  posture: Posture;
  question: ResearchQuestionRef | null;
}
