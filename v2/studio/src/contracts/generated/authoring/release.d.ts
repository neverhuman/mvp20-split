/* Generated from the published Python-owned serialization schema. Do not edit. */

/**
 * @minItems 1
 * @maxItems 16
 */
export type AntiExamples = string[];
export type AuthorityCeiling = "synthetic_only" | "evidence_proposal";
export type Mode = "none" | "opaque_artifact";
/**
 * @maxItems 64
 */
export type ReadableSchemaSha256 = string[];
export type Egress = DeniedEgress | AllowedEgress;
export type Mode1 = "deny";
/**
 * @minItems 1
 * @maxItems 64
 */
export type Hosts = string[];
export type Mode2 = "allowlist";
/**
 * @minItems 1
 * @maxItems 16
 */
export type Examples = string[];
export type Reproducibility = "deterministic" | "seeded" | "nondeterministic";
/**
 * @minItems 1
 * @maxItems 2
 */
export type Architectures = ("x86_64" | "aarch64")[];
export type CpuMillicores = number;
export type GpuCount = number;
export type MaxBatchSize = number;
export type MaxParallelInvocations = number;
export type MemoryMib = number;
/**
 * @minItems 1
 * @maxItems 2
 */
export type OperatingSystems = ("linux" | "windows")[];
export type TimeoutSeconds = number;
export type SchemaVersion = "1";
/**
 * @minItems 1
 * @maxItems 64
 */
export type Applicability = string[];
export type CapabilityId = string;
export type ContractVersion = "1";
export type ImageSha256 = string;
export type Release = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Name = string;
export type Representation = string;
export type Required = boolean;
export type Unit = string;
/**
 * @maxItems 64
 */
export type Inputs = Port[];
/**
 * @maxItems 64
 */
export type Outputs = Port[];
export type Purpose = string;
export type SchemaVersion1 = "1";
export type SideEffects = "pure" | "idempotent" | "external";
export type DescriptorSha256 = string;
export type Port1 = string;
/**
 * @maxItems 64
 */
export type InputSchemas = PortSchemaLock[];
/**
 * @maxItems 64
 */
export type OutputSchemas = PortSchemaLock[];
export type SchemaVersion2 = "1";
export type Revision = number;
export type ProjectId = string;
export type TenantId = string;
export type Status = "registered" | "active" | "draining" | "revoked";

export interface ReleaseSnapshot {
  descriptor: ReleaseDescriptor;
  lock: LockEntry;
  revision: Revision;
  scope: Scope;
  status: Status;
}
export interface ReleaseDescriptor {
  anti_examples: AntiExamples;
  authority_ceiling: AuthorityCeiling;
  checkpoint: CheckpointCompatibility;
  egress: Egress;
  examples: Examples;
  reproducibility: Reproducibility;
  resources: ResourceBounds;
  schema_version: SchemaVersion;
  tool: ToolDescriptor;
}
export interface CheckpointCompatibility {
  mode: Mode;
  readable_schema_sha256: ReadableSchemaSha256;
}
export interface DeniedEgress {
  mode: Mode1;
}
export interface AllowedEgress {
  hosts: Hosts;
  mode: Mode2;
}
export interface ResourceBounds {
  architectures: Architectures;
  cpu_millicores: CpuMillicores;
  gpu_count: GpuCount;
  max_batch_size: MaxBatchSize;
  max_parallel_invocations: MaxParallelInvocations;
  memory_mib: MemoryMib;
  operating_systems: OperatingSystems;
  timeout_seconds: TimeoutSeconds;
}
export interface ToolDescriptor {
  applicability: Applicability;
  binding: ToolBinding;
  checkpoint_schema?: SchemaRef | null;
  inputs: Inputs;
  outputs: Outputs;
  purpose: Purpose;
  schema_version: SchemaVersion1;
  side_effects: SideEffects;
}
export interface ToolBinding {
  capability_id: CapabilityId;
  contract_version: ContractVersion;
  image_sha256: ImageSha256;
  release: Release;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha256;
  version: Version;
}
export interface Port {
  name: Name;
  representation: Representation;
  required?: Required;
  schema_ref: SchemaRef;
  unit: Unit;
}
export interface LockEntry {
  checkpoint_schema: SchemaRef | null;
  descriptor_sha256: DescriptorSha256;
  input_schemas: InputSchemas;
  output_schemas: OutputSchemas;
  schema_version?: SchemaVersion2;
  tool: ToolBinding;
}
export interface PortSchemaLock {
  port: Port1;
  schema_ref: SchemaRef;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
