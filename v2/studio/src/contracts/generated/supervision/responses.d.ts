/* Generated from the published Python-owned serialization schema. Do not edit. */

export type AttemptOrdinal = number;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2561 = string;
export type SizeBytes = number;
export type CapturedBytes = number;
export type OutputComplete = boolean;
export type OutputSha256 = string;
export type ReasonCode = string | null;
export type ResponseId = string;
export type ResponseSha256 = string;
export type SelectedByWinner = boolean;
export type Status = "proposed" | "abstained" | "invalid" | "unavailable" | "policy_rejected" | "unknown";
/**
 * @maxItems 10
 */
export type Items = CheckpointResponseItem[];
export type NextCursor = string | null;
export type DecisionId = string;
export type RunId = string;
export type RequestSha256 = string;
export type SchemaVersion = "1";
export type FrontierRevision = number;
export type PlanSha256 = string;
export type Revision = number;
export type RunId1 = string;
export type Epoch = string;
export type SnapshotToken = string;
export type Total = number;

export interface CheckpointResponsePage {
  items: Items;
  next_cursor: NextCursor;
  reference: SupervisionRef;
  request_sha256: RequestSha256;
  schema_version?: SchemaVersion;
  snapshot: SupervisionInspectionCut;
  total: Total;
}
export interface CheckpointResponseItem {
  attempt_ordinal: AttemptOrdinal;
  capture: ArtifactRef | null;
  captured_bytes: CapturedBytes;
  output_complete: OutputComplete;
  output_sha256: OutputSha256;
  reason_code: ReasonCode;
  response_id: ResponseId;
  response_sha256: ResponseSha256;
  selected_by_winner: SelectedByWinner;
  status: Status;
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
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface SupervisionRef {
  decision_id: DecisionId;
  run_id: RunId;
  scope: Scope;
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
