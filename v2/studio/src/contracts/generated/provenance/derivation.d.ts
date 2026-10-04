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
/**
 * @minItems 1
 * @maxItems 128
 */
export type Inputs = ArtifactRef[];
export type SchemaVersion = "1";
export type Sha2562 = string;
export type TransformationId = string;
export type Version1 = string;
export type ActorId = string;
export type CommandFamily = string;
export type CommandId = string;
export type SchemaVersion1 = "1";
export type RequestSha256 = string;
export type SchemaVersion2 = "1";
export type UploadId = string;

/**
 * Immutable finalized lineage; reading it does not grant payload access.
 */
export interface DerivationReceipt {
  artifact: ArtifactRef;
  declaration: DerivationDeclaration;
  origin: CommandIdentity;
  request_sha256: RequestSha256;
  schema_version?: SchemaVersion2;
  upload_id: UploadId;
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
export interface DerivationDeclaration {
  inputs: Inputs;
  schema_version?: SchemaVersion;
  transformation: TransformationDescriptor;
}
/**
 * Pinned producer method/configuration digest, not a scientific attestation.
 */
export interface TransformationDescriptor {
  sha256: Sha2562;
  transformation_id: TransformationId;
  version: Version1;
}
export interface CommandIdentity {
  actor_id: ActorId;
  command_family: CommandFamily;
  command_id: CommandId;
  schema_version?: SchemaVersion1;
  scope: Scope;
}
