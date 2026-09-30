/* Generated from the published Python-owned serialization schema. Do not edit. */

export type FrontierRevision = number;
export type PlanSha256 = string;
export type Revision = number;
export type RunId = string;
export type ProjectId = string;
export type TenantId = string;
export type NextCursor = string | null;
export type ParentActivationId = string | null;
export type SchemaVersion = "1";
export type ScopeCount = number;
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
export type ParentActivationId1 = string | null;
export type ScopeKey = string;
export type Status = "active" | "completed" | "failed" | "skipped" | "blocked";
/**
 * @maxItems 100
 */
export type Scopes = GraphScopeView[];

export interface GraphScopePage {
  cut: GraphReadCut;
  next_cursor: NextCursor;
  parent_activation_id: ParentActivationId;
  schema_version?: SchemaVersion;
  scope_count: ScopeCount;
  scopes: Scopes;
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
export interface GraphScopeView {
  definition_path: DefinitionPath;
  node_count: NodeCount;
  occurrences: Occurrences;
  parent_activation_id: ParentActivationId1;
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
