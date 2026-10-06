/* Generated from the published Python-owned serialization schema. Do not edit. */

export type CheckpointId = string;
export type EligibilityReason = string | null;
export type DecisionId = string;
export type RunId = string;
export type ProjectId = string;
export type TenantId = string;
export type Requests = number;
/**
 * @minItems 1
 * @maxItems 64
 */
export type Targets = string[];
export type WinnerKind = ("model_accepted" | "fallback" | "cancelled") | null;
export type WinnerReason = string | null;
/**
 * @maxItems 10
 */
export type Items = CheckpointInspectionItem[];
export type NextCursor = string | null;
export type SchemaVersion = "1";
export type FrontierRevision = number;
export type PlanSha256 = string;
export type Revision = number;
export type RunId1 = string;
export type Epoch = string;
export type SnapshotToken = string;
export type Total = number;

export interface CheckpointInspectionPage {
  items: Items;
  next_cursor: NextCursor;
  schema_version?: SchemaVersion;
  snapshot: SupervisionInspectionCut;
  total: Total;
}
export interface CheckpointInspectionItem {
  checkpoint_id: CheckpointId;
  eligibility_reason: EligibilityReason;
  reference: SupervisionRef;
  requests: Requests;
  targets: Targets;
  winner_kind: WinnerKind;
  winner_reason: WinnerReason;
}
export interface SupervisionRef {
  decision_id: DecisionId;
  run_id: RunId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface SupervisionInspectionCut {
  cut: GraphReadCut;
  epoch: Epoch;
  snapshot_token: SnapshotToken;
}
export interface GraphReadCut {
  frontier_revision: FrontierRevision;
  plan_sha256: PlanSha256;
  revision: Revision;
  run_id: RunId1;
  scope: Scope;
}
