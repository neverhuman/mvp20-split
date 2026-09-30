/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ContentSha256 = string;
export type DraftId = string;
export type Code = string;
export type Location = string;
export type Message = string;
/**
 * @maxItems 20
 */
export type Findings = Finding[];
/**
 * @maxItems 16
 */
export type PendingChecks = string[];
export type PlanSha256 = string | null;
export type Revision = number;
export type SchemaVersion = "1";
export type ScientificAcceptance = "not_established";
export type ProjectId = string;
export type TenantId = string;
export type StructurallyValid = boolean;
export type UniverseSha256 = string;
export type ValidationId = string;

export interface DraftValidation {
  content_sha256: ContentSha256;
  draft_id: DraftId;
  findings: Findings;
  pending_checks: PendingChecks;
  plan_sha256: PlanSha256;
  revision: Revision;
  schema_version?: SchemaVersion;
  scientific_acceptance?: ScientificAcceptance;
  scope: Scope;
  structurally_valid: StructurallyValid;
  universe_sha256: UniverseSha256;
  validation_id: ValidationId;
}
export interface Finding {
  code: Code;
  location: Location;
  message: Message;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
