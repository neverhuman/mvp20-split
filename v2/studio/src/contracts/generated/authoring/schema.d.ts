/* Generated from the published Python-owned serialization schema. Do not edit. */

export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type SchemaBytesBase64 = string;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;
export type UniverseSha256 = string;

export interface DefinitionSchema {
  reference: SchemaRef;
  schema_bytes_base64: SchemaBytesBase64;
  schema_version?: SchemaVersion;
  scope: Scope;
  universe_sha256: UniverseSha256;
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
