"""Chemical structure transport only; no toolkit, ranking or scientific authority."""
from typing import Annotated, Literal
from pydantic import Field, model_validator
from amphora_contracts_core import Digest, SchemaRef, Scope, WireModel
from amphora_contracts_research import CandidateRevisionRef

Text = Annotated[str, Field(min_length=1, max_length=256)]
AtomIndex = Annotated[int, Field(ge=0, le=511)]

class StructureIdentity(WireModel):
    scope: Scope
    candidate: CandidateRevisionRef
    semantic_profile: SchemaRef
    origin: Literal["supplied"]
    representation_kind: Literal["finite_molecule"]

    @model_validator(mode="after")
    def same_scope(self):
        if self.candidate.scope != self.scope:
            raise ValueError("candidate scope mismatch")
        return self

class StructureRequest(StructureIdentity):
    wire_version: Literal["1"]
    smiles: Annotated[str, Field(min_length=1, max_length=4096)]

class Atom(WireModel):
    index: AtomIndex
    atomic_number: Annotated[int, Field(ge=1, le=118)]
    isotope: Annotated[int, Field(ge=0, le=999)]
    formal_charge: Annotated[int, Field(ge=-16, le=16)]
    explicit_hydrogens: Annotated[int, Field(ge=0, le=16)]
    implicit_hydrogens: Annotated[int, Field(ge=0, le=16)]
    aromatic: bool
    chiral_tag: Literal["CHI_UNSPECIFIED", "CHI_TETRAHEDRAL_CW", "CHI_TETRAHEDRAL_CCW"]

class Bond(WireModel):
    begin: AtomIndex
    end: AtomIndex
    order: Literal["single", "double", "triple", "aromatic"]
    stereo: Literal["STEREONONE", "STEREOZ", "STEREOE", "STEREOCIS", "STEREOTRANS"]
    stereo_atoms: Annotated[list[AtomIndex], Field(max_length=2)]

class MolecularGraph(WireModel):
    atoms: Annotated[list[Atom], Field(min_length=1, max_length=512)]
    bonds: Annotated[list[Bond], Field(max_length=1024)]

class Formula(WireModel):
    text: Text
    isotope_policy: Literal["separate_isotopes"]
    charge_policy: Literal["explicit_net_formal_charge"]
    net_formal_charge: Annotated[int, Field(ge=-2048, le=2048)]

class Depiction(WireModel):
    media_type: Literal["image/png"]
    width: Annotated[int, Field(ge=1, le=1024)]
    height: Annotated[int, Field(ge=1, le=768)]
    sha256: Digest
    png_base64: Annotated[str, Field(min_length=4, max_length=174764, pattern=r"^[A-Za-z0-9+/]*={0,2}$")]

class DerivationMethod(WireModel):
    toolkit: Literal["rdkit"]
    toolkit_version: Text
    method: Literal["finite-smiles-2d-v1"]
    environment_sha256: Digest

class DerivedStructure(WireModel):
    status: Literal["derived"]
    authority: Literal["structural_derivation"]
    method: DerivationMethod
    canonical_isomeric_smiles: Annotated[str, Field(min_length=1, max_length=8192)]
    graph: MolecularGraph
    formula: Formula
    depiction: Depiction
    warnings: Annotated[list[Literal["unspecified_stereochemistry"]], Field(max_length=1)]

class StructureFailure(WireModel):
    status: Literal["invalid", "unsupported", "error"]
    code: Literal["invalid_smiles", "unsupported_representation", "unsupported_feature", "profile_mismatch", "size_limit", "derivation_failed"]

class StructureResult(StructureIdentity):
    wire_version: Literal["1"]
    source_sha256: Digest
    outcome: Annotated[DerivedStructure | StructureFailure, Field(discriminator="status")]

__all__ = ["StructureRequest", "StructureResult", "Atom", "Bond", "MolecularGraph", "Formula", "Depiction", "DerivationMethod", "DerivedStructure", "StructureFailure"]
