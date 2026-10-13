/* Generated from the published Python-owned serialization schema. Do not edit. */

export type CandidateId = string;
export type Revision = number;
export type ProjectId = string;
export type TenantId = string;
export type Origin = "supplied";
export type Outcome = DerivedStructure | StructureFailure;
export type Authority = "structural_derivation";
export type CanonicalIsomericSmiles = string;
export type Height = number;
export type MediaType = "image/png";
export type PngBase64 = string;
export type Sha256 = string;
export type Width = number;
export type ChargePolicy = "explicit_net_formal_charge";
export type IsotopePolicy = "separate_isotopes";
export type NetFormalCharge = number;
export type Text = string;
export type Aromatic = boolean;
export type AtomicNumber = number;
export type ChiralTag = "CHI_UNSPECIFIED" | "CHI_TETRAHEDRAL_CW" | "CHI_TETRAHEDRAL_CCW";
export type ExplicitHydrogens = number;
export type FormalCharge = number;
export type ImplicitHydrogens = number;
export type Index = number;
export type Isotope = number;
/**
 * @minItems 1
 * @maxItems 512
 */
export type Atoms = Atom[];
export type Begin = number;
export type End = number;
export type Order = "single" | "double" | "triple" | "aromatic";
export type Stereo = "STEREONONE" | "STEREOZ" | "STEREOE" | "STEREOCIS" | "STEREOTRANS";
/**
 * @maxItems 2
 */
export type StereoAtoms = number[];
/**
 * @maxItems 1024
 */
export type Bonds = Bond[];
export type EnvironmentSha256 = string;
export type Method = "finite-smiles-2d-v1";
export type Toolkit = "rdkit";
export type ToolkitVersion = string;
export type Status = "derived";
/**
 * @maxItems 1
 */
export type Warnings = "unspecified_stereochemistry"[];
export type Code =
  | "invalid_smiles"
  | "unsupported_representation"
  | "unsupported_feature"
  | "profile_mismatch"
  | "size_limit"
  | "derivation_failed";
export type Status1 = "invalid" | "unsupported" | "error";
export type RepresentationKind = "finite_molecule";
export type SchemaId = string;
export type Sha2561 = string;
export type Version = "1";
export type SourceSha256 = string;
export type WireVersion = "1";

export interface StructureResult {
  candidate: CandidateRevisionRef;
  origin: Origin;
  outcome: Outcome;
  representation_kind: RepresentationKind;
  scope: Scope;
  semantic_profile: SchemaRef;
  source_sha256: SourceSha256;
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
export interface DerivedStructure {
  authority: Authority;
  canonical_isomeric_smiles: CanonicalIsomericSmiles;
  depiction: Depiction;
  formula: Formula;
  graph: MolecularGraph;
  method: DerivationMethod;
  status: Status;
  warnings: Warnings;
}
export interface Depiction {
  height: Height;
  media_type: MediaType;
  png_base64: PngBase64;
  sha256: Sha256;
  width: Width;
}
export interface Formula {
  charge_policy: ChargePolicy;
  isotope_policy: IsotopePolicy;
  net_formal_charge: NetFormalCharge;
  text: Text;
}
export interface MolecularGraph {
  atoms: Atoms;
  bonds: Bonds;
}
export interface Atom {
  aromatic: Aromatic;
  atomic_number: AtomicNumber;
  chiral_tag: ChiralTag;
  explicit_hydrogens: ExplicitHydrogens;
  formal_charge: FormalCharge;
  implicit_hydrogens: ImplicitHydrogens;
  index: Index;
  isotope: Isotope;
}
export interface Bond {
  begin: Begin;
  end: End;
  order: Order;
  stereo: Stereo;
  stereo_atoms: StereoAtoms;
}
export interface DerivationMethod {
  environment_sha256: EnvironmentSha256;
  method: Method;
  toolkit: Toolkit;
  toolkit_version: ToolkitVersion;
}
export interface StructureFailure {
  code: Code;
  status: Status1;
}
export interface SchemaRef {
  schema_id: SchemaId;
  sha256: Sha2561;
  version: Version;
}
