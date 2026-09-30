/* Generated from the published Python-owned serialization schema. Do not edit. */

export type FrontierRevision = number;
export type PlanSha256 = string;
export type Revision = number;
export type RunId = string;
export type ProjectId = string;
export type TenantId = string;
export type EdgeCount = number;
export type Route = "next" | "true" | "false";
export type Source = string;
export type Target = string;
/**
 * @maxItems 1024
 */
export type Edges = GraphControlLink[];
/**
 * @maxItems 16
 */
export type DefinitionPath = string[];
export type NodeCount = number;
export type Index = number;
export type Kind = "loop";
export type NodeId = string;
export type Index1 = number;
export type Kind1 = "scatter";
export type MembershipSha256 = string;
export type NodeId1 = string;
/**
 * @maxItems 16
 */
export type Occurrences = (LoopOccurrence | ScatterOccurrence)[];
export type ParentActivationId = string | null;
export type ScopeKey = string;
export type Status = "active" | "completed" | "failed" | "skipped" | "blocked";
export type NextCursor = string | null;
export type NodeCount1 = number;
export type ActivationId = string;
export type Kind2 =
  | "invoke"
  | "branch"
  | "join"
  | "scatter"
  | "iterate"
  | "finish"
  | "await"
  | "artifact_project"
  | "artifact_materialize";
export type NodeId2 = string;
/**
 * @maxItems 16
 */
export type Occurrences1 = (LoopOccurrence | ScatterOccurrence)[];
export type SchemaVersion = "2";
export type ReasonCode = string | null;
export type Status1 = "waiting" | "ready" | "issued" | "succeeded" | "skipped" | "failed" | "blocked";
export type ChildScopeCount = number;
/**
 * @maxItems 100
 */
export type Nodes = GraphTopologyNode[];
export type FocusActivationId = string | null;
export type Radius = number;
export type SchemaVersion1 = "1";

export interface GraphTopologyPage {
  cut: GraphReadCut;
  edge_count: EdgeCount;
  edges: Edges;
  graph_scope: GraphScopeView;
  next_cursor: NextCursor;
  node_count: NodeCount1;
  nodes: Nodes;
  query: GraphTopologyQuery;
  schema_version?: SchemaVersion1;
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
export interface GraphControlLink {
  route: Route;
  source: Source;
  target: Target;
}
export interface GraphScopeView {
  definition_path: DefinitionPath;
  node_count: NodeCount;
  occurrences: Occurrences;
  parent_activation_id: ParentActivationId;
  scope_key: ScopeKey;
  status: Status;
}
export interface LoopOccurrence {
  index: Index;
  kind: Kind;
  node_id: NodeId;
}
export interface ScatterOccurrence {
  index: Index1;
  kind: Kind1;
  membership_sha256: MembershipSha256;
  node_id: NodeId1;
}
export interface GraphTopologyNode {
  activation: GraphNodeViewV3;
  child_scope_count: ChildScopeCount;
}
export interface GraphNodeViewV3 {
  activation_id: ActivationId;
  kind: Kind2;
  path: ActivationPath;
  reason_code: ReasonCode;
  status: Status1;
}
export interface ActivationPath {
  node_id: NodeId2;
  occurrences?: Occurrences1;
  schema_version: SchemaVersion;
}
export interface GraphTopologyQuery {
  focus_activation_id?: FocusActivationId;
  radius?: Radius;
}
