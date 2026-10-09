/* Generated from the published Python-owned serialization schema. Do not edit. */

export type MaximumDeadlineSeconds = number;
export type MaximumInvocations = number;
export type ProfileId = string;
export type Sha256 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Title = string;
export type CapabilityId = string;
export type ContractVersion = "1";
export type ImageSha256 = string;
export type Release = string;
/**
 * @minItems 1
 * @maxItems 64
 */
export type Tools = ToolBinding[];
/**
 * @maxItems 32
 */
export type Profiles = LaunchProfileView[];
export type WireVersion = "1";

export interface LaunchProfileCatalog {
  profiles: Profiles;
  scope: Scope;
  wire_version?: WireVersion;
}
export interface LaunchProfileView {
  maximum_deadline_seconds: MaximumDeadlineSeconds;
  maximum_invocations: MaximumInvocations;
  reference: LaunchProfileRef;
  scope: Scope;
  title: Title;
  tools: Tools;
}
export interface LaunchProfileRef {
  profile_id: ProfileId;
  sha256: Sha256;
  version: Version;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface ToolBinding {
  capability_id: CapabilityId;
  contract_version: ContractVersion;
  image_sha256: ImageSha256;
  release: Release;
}
