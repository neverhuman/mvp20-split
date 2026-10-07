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
export type EngagementId = string;
export type Ordinal = number;
export type RequestSha256 = string;
export type CapturedBytes = number;
export type OutputComplete = boolean;
export type OutputSha256 = string;
export type Action = "abstain" | "request_evidence" | "propose_knowledge_change" | "propose_campaign";
export type PayloadJson = string;
export type PayloadSha256 = string;
export type Rationale = string;
export type SchemaVersion = "1";
export type ReasonCode = string | null;
export type SchemaVersion1 = "2";
export type Status = "proposed" | "abstained" | "invalid" | "unavailable" | "policy_rejected" | "unknown";
export type AccountingUnits = number | null;
export type Certainty = "reported" | "unknown";
export type InputTokens = number | null;
export type OutputTokens = number | null;
export type DecisionId = string;
export type RunId = string;
export type RequestSha2561 = string;
export type ResponseId = string;
export type SchemaVersion2 = "1";

export interface SupervisionResponse {
  capture: ArtifactRef | null;
  observation: TaskProviderObservation;
  reference: SupervisionRef;
  request_sha256: RequestSha2561;
  response_id: ResponseId;
  schema_version?: SchemaVersion2;
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
export interface TaskProviderObservation {
  attempt: ProviderAttemptRef;
  captured_bytes: CapturedBytes;
  output_complete: OutputComplete;
  output_sha256: OutputSha256;
  proposal: TypedProposal | null;
  reason_code: ReasonCode;
  schema_version?: SchemaVersion1;
  status: Status;
  usage: ProviderUsage;
}
export interface ProviderAttemptRef {
  engagement: EngagementRef;
  ordinal: Ordinal;
  request_sha256: RequestSha256;
}
export interface EngagementRef {
  engagement_id: EngagementId;
  scope: Scope;
}
export interface TypedProposal {
  action: Action;
  output_schema: SchemaRef;
  payload_json: PayloadJson;
  payload_sha256: PayloadSha256;
  rationale: Rationale;
  schema_version?: SchemaVersion;
}
export interface ProviderUsage {
  accounting_units: AccountingUnits;
  certainty: Certainty;
  input_tokens: InputTokens;
  output_tokens: OutputTokens;
}
export interface SupervisionRef {
  decision_id: DecisionId;
  run_id: RunId;
  scope: Scope;
}
