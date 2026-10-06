/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2561 = string;
export type SizeBytes = number;
export type Required = boolean;
export type Role = "constraint" | "source" | "capability" | "knowledge" | "result";
export type Kind = "included";
export type Kind1 = "omitted";
export type Reason = "budget" | "not_relevant" | "unavailable" | "not_authorized";
/**
 * @maxItems 10
 */
export type Items = (IncludedCheckpointContext | OmittedCheckpointContext)[];
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

export interface CheckpointContextPage {
  items: Items;
  next_cursor: NextCursor;
  reference: SupervisionRef;
  request_sha256: RequestSha256;
  schema_version?: SchemaVersion;
  snapshot: SupervisionInspectionCut;
  total: Total;
}
export interface IncludedCheckpointContext {
  entry: ContextEntry;
  kind: Kind;
}
export interface ContextEntry {
  artifact: ArtifactRef;
  required: Required;
  role: Role;
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
export interface OmittedCheckpointContext {
  kind: Kind1;
  omission: ContextOmission;
}
export interface ContextOmission {
  artifact: ArtifactRef;
  reason: Reason;
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
