/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ActorId = string;
export type ChangeId = string;
export type Decision = AcceptedDecision | FailedDecision;
export type ChangeId1 = string;
export type GraphId = string;
export type ProjectId = string;
export type TenantId = string;
export type Position = number;
export type Sha256 = string;
export type Revision = number;
export type Sha2561 = string;
export type Outcome = "accepted";
export type Code = string;
export type Location = string;
export type Message = string;
/**
 * @minItems 1
 * @maxItems 64
 */
export type Findings = Finding[];
export type Outcome1 = "rejected" | "conflict";
export type RequestSha256 = string;
export type WireVersion = "1";
export type ChangeId2 = string;
export type Description = string;
export type Sha2562 = string;
export type TraceId = string;
/**
 * @minItems 1
 * @maxItems 64
 */
export type ConversionTraces = ConversionTraceRef[];
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha2563 = string;
export type Version = "1";
export type Sha2564 = string;
export type SizeBytes = number;
/**
 * @maxItems 16
 */
export type InterpretationArtifacts = ArtifactRef[];
export type End = number;
export type Sha2565 = string;
export type RevisionId = string;
export type SourceId = string;
export type Start = number;
export type Unit = "byte";
/**
 * @minItems 1
 * @maxItems 64
 */
export type Spans = SourceSpan[];
export type EntityType = string;
export type Label = string;
export type EntityId = string;
export type Revision1 = number;
export type Operation = "add_entity";
export type Polarity = "affirmed" | "negated";
export type Posture = "reported" | "hypothesis" | "unresolved";
export type Predicate = string;
export type AssertionId = string;
export type Revision2 = number;
export type NeedId = string;
export type Revision3 = number;
export type QuestionId = string;
export type Revision4 = number;
export type Role = "proposed_answer" | "support" | "contradiction" | "context";
/**
 * @maxItems 32
 */
export type ResearchLinks = QuestionEvidenceLink[];
export type Statement = string;
export type Operation1 = "add_assertion";
export type Operation2 = "correct_assertion";
export type Operation3 = "retract_assertion";
export type Operation4 = "merge_entities";
export type Operation5 = "revise_entity_context";
/**
 * @minItems 1
 * @maxItems 128
 */
export type Operations = (
  AddEntity | AddAssertion | CorrectAssertion | RetractAssertion | MergeEntities | ReviseEntityContext
)[];
export type PolicyId = string;
export type Sha2566 = string;
export type Version1 = string;
export type Rationale = string;
export type Sha2567 = string;
export type Version2 = string;
export type VocabularyId = string;
export type WireVersion1 = "1";
export type RegisteredAt = string;
export type RequestSha2561 = string;
export type WireVersion2 = "1";

export interface GraphProposalStatus {
  actor_id: ActorId;
  decision: GraphChangeDecision | null;
  proposal: GraphChangeProposal;
  registered_at: RegisteredAt;
  request_sha256: RequestSha2561;
  wire_version: WireVersion2;
}
export interface GraphChangeDecision {
  change_id: ChangeId;
  decision: Decision;
  graph: DomainGraphRef;
  request_sha256: RequestSha256;
  wire_version: WireVersion;
}
export interface AcceptedDecision {
  head: DomainHead;
  outcome: Outcome;
}
export interface DomainHead {
  change: AcceptedChangeRef;
  snapshot: DomainRevisionRef;
}
export interface AcceptedChangeRef {
  change_id: ChangeId1;
  graph: DomainGraphRef;
  position: Position;
  sha256: Sha256;
}
export interface DomainGraphRef {
  graph_id: GraphId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface DomainRevisionRef {
  graph: DomainGraphRef;
  revision: Revision;
  sha256: Sha2561;
}
export interface FailedDecision {
  findings: Findings;
  outcome: Outcome1;
}
export interface Finding {
  code: Code;
  location: Location;
  message: Message;
}
export interface GraphChangeProposal {
  base: DomainHead | null;
  change_id: ChangeId2;
  description: Description;
  graph: DomainGraphRef;
  grounding: ClaimGrounding;
  operations: Operations;
  policy: StructuralPolicyRef;
  rationale: Rationale;
  vocabulary: VocabularyRef;
  wire_version: WireVersion1;
}
export interface ClaimGrounding {
  conversion_traces: ConversionTraces;
  interpretation_artifacts: InterpretationArtifacts;
  spans: Spans;
}
export interface ConversionTraceRef {
  scope: Scope;
  sha256: Sha2562;
  trace_id: TraceId;
}
export interface ArtifactRef {
  artifact_id: ArtifactId;
  media_type: MediaType;
  schema_ref: SchemaRef;
  scope: Scope;
  sha256: Sha2564;
  size_bytes: SizeBytes;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha2563;
  version: Version;
}
/**
 * Half-open byte range; owner verifies ordering, bounds and exact content.
 */
export interface SourceSpan {
  end: End;
  sha256: Sha2565;
  source: SourceRevisionRef;
  start: Start;
  unit: Unit;
}
export interface SourceRevisionRef {
  raw: ArtifactRef;
  revision_id: RevisionId;
  scope: Scope;
  source_id: SourceId;
}
export interface AddEntity {
  entity: DomainEntity;
  operation: Operation;
}
export interface DomainEntity {
  context: ArtifactRef;
  entity_type: EntityType;
  label: Label;
  reference: EntityRevisionRef;
  supersedes: EntityRevisionRef | null;
}
export interface EntityRevisionRef {
  entity_id: EntityId;
  graph: DomainGraphRef;
  revision: Revision1;
}
export interface AddAssertion {
  assertion: DomainAssertion;
  operation: Operation1;
}
export interface DomainAssertion {
  applicability: ArtifactRef;
  grounding: ClaimGrounding;
  object: EntityRevisionRef;
  polarity: Polarity;
  posture: Posture;
  predicate: Predicate;
  reference: AssertionRevisionRef;
  research_links: ResearchLinks;
  statement: Statement;
  subject: EntityRevisionRef;
  supersedes: AssertionRevisionRef | null;
}
export interface AssertionRevisionRef {
  assertion_id: AssertionId;
  graph: DomainGraphRef;
  revision: Revision2;
}
export interface QuestionEvidenceLink {
  answer_proposal: ArtifactRef | null;
  need: EvidenceNeedRef | null;
  question: ResearchQuestionRef;
  role: Role;
  validation_method: SchemaRef | null;
}
export interface EvidenceNeedRef {
  need_id: NeedId;
  revision: Revision3;
  scope: Scope;
}
export interface ResearchQuestionRef {
  question_id: QuestionId;
  revision: Revision4;
  scope: Scope;
}
export interface CorrectAssertion {
  operation: Operation2;
  prior: AssertionRevisionRef;
  replacement: DomainAssertion;
}
export interface RetractAssertion {
  assertion: AssertionRevisionRef;
  operation: Operation3;
}
export interface MergeEntities {
  operation: Operation4;
  source: EntityRevisionRef;
  target: EntityRevisionRef;
}
export interface ReviseEntityContext {
  operation: Operation5;
  prior: EntityRevisionRef;
  replacement: DomainEntity;
}
export interface StructuralPolicyRef {
  policy_id: PolicyId;
  sha256: Sha2566;
  version: Version1;
}
export interface VocabularyRef {
  sha256: Sha2567;
  version: Version2;
  vocabulary_id: VocabularyId;
}
