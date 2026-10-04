/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Completeness = "complete" | "partial" | "unknown";
export type DeliveryId = string;
export type IssuerId = string;
export type ConfigurationSha256 = string;
export type ConnectorId = string;
export type ConnectorVersion = string;
export type Format = "utf8_document" | "synthetic_lab_json";
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type ProjectId = string;
export type TenantId = string;
export type Sha2561 = string;
export type SizeBytes = number;
export type RevisionId = string;
export type SourceId = string;
export type Revision = number;
export type RightsId = string;
export type WireVersion = "1";

export interface SourceRevision {
  completeness: Completeness;
  delivery: DeliveryIdentity;
  method: AcquisitionMethod;
  reference: SourceRevisionRef;
  rights: RightsRevisionRef;
  supersedes: SourceRevisionRef | null;
  wire_version: WireVersion;
}
export interface DeliveryIdentity {
  delivery_id: DeliveryId;
  issuer_id: IssuerId;
}
export interface AcquisitionMethod {
  configuration_sha256: ConfigurationSha256;
  connector_id: ConnectorId;
  connector_version: ConnectorVersion;
  format: Format;
}
export interface SourceRevisionRef {
  raw: ArtifactRef;
  revision_id: RevisionId;
  scope: Scope;
  source_id: SourceId;
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
export interface RightsRevisionRef {
  revision: Revision;
  rights_id: RightsId;
  scope: Scope;
}
