/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ChainId = string;
export type IssuerId = string;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;
export type Ordinal = number;
export type RecordSha256 = string;
export type SchemaVersion1 = "1";
export type WireVersion = "1";

export interface SelectReasoningReceipt {
  chain: ReceiptChainRef;
  revision: ReceiptRevisionRef | null;
  wire_version: WireVersion;
}
export interface ReceiptChainRef {
  chain_id: ChainId;
  issuer_id: IssuerId;
  schema_version?: SchemaVersion;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface ReceiptRevisionRef {
  chain: ReceiptChainRef;
  ordinal: Ordinal;
  record_sha256: RecordSha256;
  schema_version?: SchemaVersion1;
}
