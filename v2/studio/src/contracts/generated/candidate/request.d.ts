/* Generated from the published Python-owned serialization schema. Do not edit. */

export type CandidateId = string;
export type Revision = number;
export type ProjectId = string;
export type TenantId = string;
export type Origin = "supplied";
export type RepresentationKind = "finite_molecule";
export type SchemaId = string;
export type Sha256 = string;
export type Version = "1";
export type Smiles = string;
export type WireVersion = "1";

export interface StructureRequest {
  candidate: CandidateRevisionRef;
  origin: Origin;
  representation_kind: RepresentationKind;
  scope: Scope;
  semantic_profile: SchemaRef;
  smiles: Smiles;
  wire_version: WireVersion;
}
export interface CandidateRevisionRef {
  candidate_id: CandidateId;
  revision: Revision;
  scope: Scope;
}
export interface Scope {
  project_id: ProjectId;
  tenant_id: TenantId;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha256;
  version: Version;
}
