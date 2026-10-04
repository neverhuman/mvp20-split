/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Detail = GraphEntityDetail | GraphAssertionDetail;
export type EntityId = string;
export type GraphId = string;
export type ProjectId = string;
export type TenantId = string;
export type Revision = number;
export type IsLatest = boolean;
export type Kind = "entity";
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Sha2561 = string;
export type SizeBytes = number;
export type EntityType = string;
export type Label = string;
export type IsLatest1 = boolean;
export type Kind1 = "assertion";
export type Sha2562 = string;
export type TraceId = string;
/**
 * @minItems 1
 * @maxItems 64
 */
export type ConversionTraces = ConversionTraceRef[];
/**
 * @maxItems 16
 */
export type InterpretationArtifacts = ArtifactRef[];
export type End = number;
export type Sha2563 = string;
export type RevisionId = string;
export type SourceId = string;
export type Start = number;
export type Unit = "byte";
/**
 * @minItems 1
 * @maxItems 64
 */
export type Spans = SourceSpan[];
export type Polarity = "affirmed" | "negated";
export type Posture = "reported" | "hypothesis" | "unresolved";
export type Predicate = string;
export type AssertionId = string;
export type Revision1 = number;
export type NeedId = string;
export type Revision2 = number;
export type QuestionId = string;
export type Revision3 = number;
export type Role = "proposed_answer" | "support" | "contradiction" | "context";
/**
 * @maxItems 32
 */
export type ResearchLinks = QuestionEvidenceLink[];
export type Statement = string;
export type Retracted = boolean;
export type Revision4 = number;
export type Sha2564 = string;
export type Selection = GraphEntitySelection | GraphAssertionSelection;
export type Kind2 = "entity";
export type Kind3 = "assertion";
export type WireVersion = "1";
export type WireVersion1 = "1";

export interface GraphObjectDetail {
  detail: Detail;
  request: GraphObjectRequest;
  wire_version: WireVersion1;
}
export interface GraphEntityDetail {
  alias_target: EntityRevisionRef | null;
  is_latest: IsLatest;
  kind: Kind;
  record: DomainEntity;
}
export interface EntityRevisionRef {
  entity_id: EntityId;
  graph: DomainGraphRef;
  revision: Revision;
}
export interface DomainGraphRef {
  graph_id: GraphId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface DomainEntity {
  context: ArtifactRef;
  entity_type: EntityType;
  label: Label;
  reference: EntityRevisionRef;
  supersedes: EntityRevisionRef | null;
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
export interface GraphAssertionDetail {
  is_latest: IsLatest1;
  kind: Kind1;
  record: DomainAssertion;
  retracted: Retracted;
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
/**
 * Half-open byte range; owner verifies ordering, bounds and exact content.
 */
export interface SourceSpan {
  end: End;
  sha256: Sha2563;
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
export interface AssertionRevisionRef {
  assertion_id: AssertionId;
  graph: DomainGraphRef;
  revision: Revision1;
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
  revision: Revision2;
  scope: Scope;
}
export interface ResearchQuestionRef {
  question_id: QuestionId;
  revision: Revision3;
  scope: Scope;
}
export interface GraphObjectRequest {
  revision: DomainRevisionRef;
  selection: Selection;
  wire_version: WireVersion;
}
export interface DomainRevisionRef {
  graph: DomainGraphRef;
  revision: Revision4;
  sha256: Sha2564;
}
export interface GraphEntitySelection {
  kind: Kind2;
  reference: EntityRevisionRef;
}
export interface GraphAssertionSelection {
  kind: Kind3;
  reference: AssertionRevisionRef;
}
