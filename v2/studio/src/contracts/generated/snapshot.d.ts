/* Generated from the published Python-owned serialization schema. Do not edit. */

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
export type Status = "waiting" | "ready" | "issued" | "succeeded" | "skipped" | "failed" | "blocked";
/**
 * @maxItems 100
 */
export type Nodes = GraphNodeViewV3[];
export type SchemaVersion1 = "1";
export type Limit = number;
export type Reserved = number;
export type Spent = number;
export type FrontierRevision = number;
export type PlanSha256 = string;
export type Revision = number;
export type RunId = string;
export type ProjectId = string;
export type TenantId = string;
export type EventCursor = string;
export type NodeCount = number;
export type FrontierOnly = boolean;
export type ScopeKey = string | null;
export type SnapshotToken = string;
export type Status1 = "running" | "completed" | "cancelled" | "failed" | "blocked";

export interface GraphSnapshotPage {
  next_cursor: NextCursor;
  nodes: Nodes;
  schema_version?: SchemaVersion1;
  snapshot: GraphReadSnapshot;
}
export interface GraphNodeViewV3 {
  activation_id: ActivationId;
  kind: Kind;
  path: ActivationPath;
  reason_code: ReasonCode;
  status: Status;
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
export interface GraphReadSnapshot {
  budget: GraphReadBudget;
  cut: GraphReadCut;
  event_cursor: EventCursor;
  node_count: NodeCount;
  query: GraphReadQuery;
  snapshot_token: SnapshotToken;
  status: Status1;
}
export interface GraphReadBudget {
  limit: Limit;
  reserved: Reserved;
  spent: Spent;
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
export interface GraphReadQuery {
  frontier_only?: FrontierOnly;
  scope_key?: ScopeKey;
}
