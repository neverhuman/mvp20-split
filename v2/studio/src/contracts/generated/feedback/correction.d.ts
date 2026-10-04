/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ActorId = string;
export type ChainId = string;
export type IssuerId = string;
export type SchemaVersion = "1";
export type ProjectId = string;
export type TenantId = string;
export type ChangeId = string;
export type IssuerId1 = string;
export type Outcome = AcceptedEvidence | RejectedEvidence | AbstainedEvidence | SupersededEvidence;
export type ArtifactId = string;
export type MediaType = string;
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Sha2561 = string;
export type SizeBytes = number;
export type Kind = "artifact";
export type Representation = string;
export type Unit = string;
export type Status = "accepted";
export type ReasonCode = string;
export type Status1 = "rejected";
export type ReasonCode1 = string;
export type Status2 = "abstained";
export type ReasonCode2 = string;
export type ReplacementRevision = string;
export type Status3 = "superseded";
export type Purpose = string;
export type ReceiptId = string;
export type Revision = string;
export type SchemaVersion1 = "1";
export type Ordinal = number;
export type Ordinal1 = number;
export type RecordSha256 = string;
export type SchemaVersion2 = "1";
export type ReasonCode3 = string;
export type SchemaVersion3 = "1";
export type SchemaVersion4 = "1";

export interface ReceiptCorrectionView {
  record: ReceiptCorrection;
  reference: ReceiptRevisionRef;
  schema_version?: SchemaVersion4;
}
export interface ReceiptCorrection {
  actor_id: ActorId;
  chain: ReceiptChainRef;
  change_id: ChangeId;
  notice: DomainReceipt | null;
  ordinal: Ordinal;
  predecessor: ReceiptRevisionRef | null;
  reason_code: ReasonCode3;
  receipt: DomainReceipt;
  schema_version?: SchemaVersion3;
  source_receipt: DomainReceipt;
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
export interface DomainReceipt {
  issuer_id: IssuerId1;
  outcome: Outcome;
  purpose: Purpose;
  receipt_id: ReceiptId;
  revision: Revision;
  schema_version?: SchemaVersion1;
  scope: Scope;
  subject: ArtifactRef;
}
export interface AcceptedEvidence {
  output: ArtifactConstant;
  status: Status;
}
export interface ArtifactConstant {
  artifact: ArtifactRef;
  kind: Kind;
  representation: Representation;
  unit: Unit;
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
export interface RejectedEvidence {
  reason_code: ReasonCode;
  status: Status1;
}
export interface AbstainedEvidence {
  reason_code: ReasonCode1;
  status: Status2;
}
export interface SupersededEvidence {
  reason_code: ReasonCode2;
  replacement_revision: ReplacementRevision;
  status: Status3;
}
export interface ReceiptRevisionRef {
  chain: ReceiptChainRef;
  ordinal: Ordinal1;
  record_sha256: RecordSha256;
  schema_version?: SchemaVersion2;
}
