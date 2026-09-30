/* Generated from the published Python-owned serialization schema. Do not edit. */

export type AttemptId = string;
export type CanonicalResult = boolean;
export type CompletionId = string | null;
export type Fence = number;
export type InvocationId = string;
export type Settled = boolean;
export type Status = "leased" | "succeeded" | "abstained" | "failed" | "expired" | "cancelled" | "uncertain";
export type WorkerId = string;
/**
 * @maxItems 100
 */
export type Attempts = GraphAttemptView[];
export type FrontierRevision = number;
export type PlanSha256 = string;
export type Revision = number;
export type RunId = string;
export type ProjectId = string;
export type TenantId = string;
export type NextCursor = string | null;
export type ActivationId = string;
export type Kind =
  | "invoke"
  | "branch"
  | "join"
  | "scatter"
  | "iterate"
  | "finish"
  | "await"
  | "artifact_project"
  | "artifact_materialize";
export type NodeId = string;
export type Index = number;
export type Kind1 = "loop";
export type NodeId1 = string;
export type Index1 = number;
export type Kind2 = "scatter";
export type MembershipSha256 = string;
export type NodeId2 = string;
/**
 * @maxItems 16
 */
export type Occurrences = (LoopOccurrence | ScatterOccurrence)[];
export type SchemaVersion = "2";
export type ReasonCode = string | null;
export type Status1 = "waiting" | "ready" | "issued" | "succeeded" | "skipped" | "failed" | "blocked";
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Sha2561 = string;
export type SizeBytes = number;
export type ItemCount = number;
export type Kind3 = "boolean" | "integer" | "number" | "string" | "artifact" | "collection";
export type MissingCount = number;
export type Port = string;
/**
 * @maxItems 64
 */
export type Outputs = GraphOutputSummary[];
export type ParentActivationId = string | null;
export type SchemaVersion1 = "1";
export type ScopeKey = string;

export interface GraphNodeDetail {
  attempts: Attempts;
  cut: GraphReadCut;
  next_cursor: NextCursor;
  node: GraphNodeViewV3;
  outputs: Outputs;
  parent_activation_id: ParentActivationId;
  schema_version?: SchemaVersion1;
  scope_key: ScopeKey;
}
export interface GraphAttemptView {
  attempt_id: AttemptId;
  canonical_result: CanonicalResult;
  completion_id: CompletionId;
  fence: Fence;
  invocation_id: InvocationId;
  settled: Settled;
  status: Status;
  worker_id: WorkerId;
}
export interface GraphReadCut {
  frontier_revision: FrontierRevision;
  plan_sha256: PlanSha256;
  revision: Revision;
  run_id: RunId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface GraphNodeViewV3 {
  activation_id: ActivationId;
  kind: Kind;
  path: ActivationPath;
  reason_code: ReasonCode;
  status: Status1;
}
export interface ActivationPath {
  node_id: NodeId;
  occurrences?: Occurrences;
  schema_version: SchemaVersion;
}
export interface LoopOccurrence {
  index: Index;
  kind: Kind1;
  node_id: NodeId1;
}
export interface ScatterOccurrence {
  index: Index1;
  kind: Kind2;
  membership_sha256: MembershipSha256;
  node_id: NodeId2;
}
export interface GraphOutputSummary {
  artifact?: ArtifactRef | null;
  item_count: ItemCount;
  kind: Kind3;
  missing_count: MissingCount;
  port: Port;
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
