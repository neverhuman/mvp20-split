/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ObservationSha256 = string;
export type Ordinal = number;
export type Status = "proposed" | "abstained" | "invalid" | "unavailable" | "policy_rejected" | "unknown";
/**
 * @maxItems 16
 */
export type Attempts = CheckpointInspectionAttempt[];
export type ContextEntries = number;
export type ContextOmissions = number;
export type Disposition = ("repair" | "fallback") | null;
export type DispositionReason = string | null;
export type EngagementId = string;
export type ProjectId = string;
export type TenantId = string;
export type AccountingUnit = string;
export type MaxAttempts = number;
export type MaxInputTokens = number;
export type MaxOutputTokens = number;
export type TotalAccountingUnits = number;
export type TotalTokens = number;
export type Ordinal1 = number;
export type ParentRequestSha256 = string | null;
export type RootRequestSha256 = string | null;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Sha2561 = string;
export type SizeBytes = number;
export type ContextWindowTokens = number;
export type ModelId = string;
export type ModelRevision = string;
export type ProviderId = string;
export type PlanningRequestSha256 = string;
export type ReportStopReason =
  | (
      | "proposed"
      | "abstained"
      | "policy_rejected"
      | "attempt_limit"
      | "checkpoint_deadline"
      | "execution_processing_unavailable"
      | "required_artifact_unavailable"
      | "required_packet_size"
      | "required_input_limit"
      | "budget_template_unavailable"
      | "provider_unconfigured"
      | "token_budget_exhausted"
      | "accounting_budget_exhausted"
      | "provider_usage_overage"
      | "repair_attempt_budget_exhausted"
      | "repair_token_budget_exhausted"
      | "repair_accounting_budget_exhausted"
    )
  | null;
export type RequestSha256 = string;
export type Responses = number;
/**
 * @maxItems 10
 */
export type Items = CheckpointRequestItem[];
export type NextCursor = string | null;
export type DecisionId = string;
export type RunId = string;
export type SchemaVersion = "1";
export type FrontierRevision = number;
export type PlanSha256 = string;
export type Revision = number;
export type RunId1 = string;
export type Epoch = string;
export type SnapshotToken = string;
export type Total = number;

export interface CheckpointRequestPage {
  items: Items;
  next_cursor: NextCursor;
  reference: SupervisionRef;
  schema_version?: SchemaVersion;
  snapshot: SupervisionInspectionCut;
  total: Total;
}
export interface CheckpointRequestItem {
  attempts: Attempts;
  context_entries: ContextEntries;
  context_omissions: ContextOmissions;
  disposition: Disposition;
  disposition_reason: DispositionReason;
  engagement: EngagementRef;
  limits: CallLimits;
  lineage: SupervisionLineage;
  model: ModelBinding;
  planning_request_sha256: PlanningRequestSha256;
  prompt: ArtifactRef;
  report_stop_reason: ReportStopReason;
  request_sha256: RequestSha256;
  responses: Responses;
}
export interface CheckpointInspectionAttempt {
  observation_sha256: ObservationSha256;
  ordinal: Ordinal;
  status: Status;
}
export interface EngagementRef {
  engagement_id: EngagementId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface CallLimits {
  accounting_unit: AccountingUnit;
  max_attempts: MaxAttempts;
  max_input_tokens: MaxInputTokens;
  max_output_tokens: MaxOutputTokens;
  total_accounting_units: TotalAccountingUnits;
  total_tokens: TotalTokens;
}
export interface SupervisionLineage {
  ordinal: Ordinal1;
  parent_request_sha256: ParentRequestSha256;
  root_request_sha256: RootRequestSha256;
}
export interface ModelBinding {
  configuration: ArtifactRef;
  context_window_tokens: ContextWindowTokens;
  model_id: ModelId;
  model_revision: ModelRevision;
  provider_id: ProviderId;
  tokenizer: SchemaRef;
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
