/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ActorId = string;
export type Outcome = AssessmentPublicationPending | AssessmentPublicationFailed | AssessmentPublished;
export type Status = "pending";
export type Code = string;
export type ExternalEffects = "possible";
export type Status1 = "failed";
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
export type ActorId1 = string;
export type CommandFamily = string;
export type CommandId = string;
export type SchemaVersion1 = "1";
export type RequestSha256 = string;
export type SchemaVersion2 = "1";
export type UploadId = string;
export type IssuerId = string;
export type Outcome1 = AcceptedEvidence | RejectedEvidence | AbstainedEvidence | SupersededEvidence;
export type Kind = "artifact";
export type Representation = string;
export type Unit = string;
export type Status2 = "accepted";
export type ReasonCode = string;
export type Status3 = "rejected";
export type ReasonCode1 = string;
export type Status4 = "abstained";
export type ReasonCode2 = string;
export type ReplacementRevision = string;
export type Status5 = "superseded";
export type Purpose = string;
export type ReceiptId = string;
export type Revision = string;
export type SchemaVersion3 = "1";
export type Status6 = "published";
export type AssessmentId = string;
export type WireVersion = "1";
export type WireVersion1 = "1";

export interface AssessmentPublicationStatus {
  actor_id: ActorId;
  outcome: Outcome;
  request: AssessmentPublicationRequest;
  wire_version: WireVersion1;
}
export interface AssessmentPublicationPending {
  status: Status;
}
export interface AssessmentPublicationFailed {
  code: Code;
  external_effects: ExternalEffects;
  status: Status1;
}
export interface AssessmentPublished {
  derivation: DerivationReceipt;
  receipt: DomainReceipt;
  status: Status6;
}
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
  actor_id: ActorId1;
  command_family: CommandFamily;
  command_id: CommandId;
  schema_version?: SchemaVersion1;
  scope: Scope;
}
export interface DomainReceipt {
  issuer_id: IssuerId;
  outcome: Outcome1;
  purpose: Purpose;
  receipt_id: ReceiptId;
  revision: Revision;
  schema_version?: SchemaVersion3;
  scope: Scope;
  subject: ArtifactRef;
}
export interface AcceptedEvidence {
  output: ArtifactConstant;
  status: Status2;
}
export interface ArtifactConstant {
  artifact: ArtifactRef;
  kind: Kind;
  representation: Representation;
  unit: Unit;
}
export interface RejectedEvidence {
  reason_code: ReasonCode;
  status: Status3;
}
export interface AbstainedEvidence {
  reason_code: ReasonCode1;
  status: Status4;
}
export interface SupersededEvidence {
  reason_code: ReasonCode2;
  replacement_revision: ReplacementRevision;
  status: Status5;
}
export interface AssessmentPublicationRequest {
  assessment_id: AssessmentId;
  scope: Scope;
  wire_version: WireVersion;
}
