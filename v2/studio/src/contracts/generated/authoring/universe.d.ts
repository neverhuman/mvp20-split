/* Generated from the published Python-owned serialization schema. Do not edit. */

export type Authority = "compiler_configuration";
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type DescriptorSha256 = string;
export type Port = string;
/**
 * @maxItems 64
 */
export type InputSchemas = PortSchemaLock[];
/**
 * @maxItems 64
 */
export type OutputSchemas = PortSchemaLock[];
export type SchemaVersion = "1";
export type CapabilityId = string;
export type ContractVersion = "1";
export type ImageSha256 = string;
export type Release = string;
/**
 * @maxItems 64
 */
export type ReviewedTools = LockEntry[];
export type SchemaVersion1 = "1";
/**
 * @maxItems 256
 */
export type Schemas = SchemaRef[];
export type ProjectId = string;
export type TenantId = string;
export type UniverseSha256 = string;

export interface DefinitionUniverse {
  authority?: Authority;
  reviewed_tools: ReviewedTools;
  schema_version?: SchemaVersion1;
  schemas: Schemas;
  scope: Scope;
  universe_sha256: UniverseSha256;
}
export interface LockEntry {
  checkpoint_schema: SchemaRef | null;
  descriptor_sha256: DescriptorSha256;
  input_schemas: InputSchemas;
  output_schemas: OutputSchemas;
  schema_version?: SchemaVersion;
  tool: ToolBinding;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha256;
  version: Version;
}
export interface PortSchemaLock {
  port: Port;
  schema_ref: SchemaRef;
}
export interface ToolBinding {
  capability_id: CapabilityId;
  contract_version: ContractVersion;
  image_sha256: ImageSha256;
  release: Release;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
