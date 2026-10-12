/* Generated from the published Python-owned serialization schema. Do not edit. */

export type CurationId = string;
export type ProjectId = string;
export type TenantId = string;
export type CreatedAt = string;
export type ActorId = string;
export type CommandFamily = string;
export type CommandId = string;
export type SchemaVersion = "1";
export type ReasonCode = string | null;
export type RequestSha256 = string;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Sha2561 = string;
export type SizeBytes = number;
/**
 * @minItems 1
 * @maxItems 16
 */
export type AcceptanceEvidence = ArtifactRef[];
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
export type SchemaVersion1 = "1";
export type CapabilityId = string;
export type ContractVersion = "1";
export type ImageSha256 = string;
export type Release = string;
export type RequestId = string;
export type Status = "pending" | "verified" | "rejected" | "indeterminate";
export type WireVersion = "1";
/**
 * @minItems 1
 * @maxItems 16
 */
export type AcceptanceCriteria = string[];
/**
 * @minItems 1
 * @maxItems 16
 */
export type Applicability = string[];
export type EvidenceNeed = string;
export type GapKey = string;
export type GraphGap = string;
export type Description = string;
export type Name = string;
export type Representation = string;
export type Unit = string | null;
/**
 * @maxItems 32
 */
export type Inputs = RequestedCapabilityPort[];
/**
 * @minItems 1
 * @maxItems 32
 */
export type Outputs = RequestedCapabilityPort[];
export type Purpose = string;
export type ProposalSha256 = string;
export type Status1 = "requested" | "fulfilled";
export type WireVersion1 = "1";

export interface CapabilityRequestView {
  curation: CurationRef;
  fulfillment: CapabilityFulfillmentReceipt | null;
  gap: CapabilityGap;
  proposal_sha256: ProposalSha256;
  reference: CapabilityRequestRef;
  status: Status1;
  wire_version?: WireVersion1;
}
export interface CurationRef {
  curation_id: CurationId;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface CapabilityFulfillmentReceipt {
  created_at: CreatedAt;
  identity: CommandIdentity;
  reason_code: ReasonCode;
  request_sha256: RequestSha256;
  specification: CapabilityFulfillmentSpecification;
  status: Status;
  wire_version?: WireVersion;
}
export interface CommandIdentity {
  actor_id: ActorId;
  command_family: CommandFamily;
  command_id: CommandId;
  schema_version?: SchemaVersion;
  scope: Scope;
}
export interface CapabilityFulfillmentSpecification {
  acceptance_evidence: AcceptanceEvidence;
  release: LockEntry;
  request: CapabilityRequestRef;
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
export interface LockEntry {
  checkpoint_schema: SchemaRef | null;
  descriptor_sha256: DescriptorSha256;
  input_schemas: InputSchemas;
  output_schemas: OutputSchemas;
  schema_version?: SchemaVersion1;
  tool: ToolBinding;
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
export interface CapabilityRequestRef {
  request_id: RequestId;
  scope: Scope;
}
/**
 * Model-local key; durable request identity is assigned by Planning.
 */
export interface CapabilityGap {
  acceptance_criteria: AcceptanceCriteria;
  applicability: Applicability;
  evidence_need: EvidenceNeed;
  gap_key: GapKey;
  graph_gap: GraphGap;
  inputs: Inputs;
  outputs: Outputs;
  purpose: Purpose;
}
export interface RequestedCapabilityPort {
  description: Description;
  name: Name;
  representation: Representation;
  schema_ref: SchemaRef | null;
  unit: Unit;
}
