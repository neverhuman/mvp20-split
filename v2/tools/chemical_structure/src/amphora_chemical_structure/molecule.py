"""Bounded finite molecular graph parsing; never completes unspecified chemistry."""
from dataclasses import dataclass
import re
from rdkit import Chem, rdBase
from amphora_contracts_chemical_structure import Atom, Bond, MolecularGraph
from .profile import StructureProblem

ORDERS={"SINGLE":"single", "DOUBLE":"double", "TRIPLE":"triple", "AROMATIC":"aromatic"}
CHIRAL={"CHI_UNSPECIFIED", "CHI_TETRAHEDRAL_CW", "CHI_TETRAHEDRAL_CCW"}
STEREO={"STEREONONE", "STEREOZ", "STEREOE", "STEREOCIS", "STEREOTRANS"}

def parse(smiles):
    settings=Chem.SmilesParserParams()
    settings.removeHs=False
    settings.parseName=False
    settings.allowCXSMILES=False
    with rdBase.BlockLogs():
        return Chem.MolFromSmiles(smiles,settings)

@dataclass(frozen=True)
class ParsedMolecule:
    mol: object
    canonical: str

    @classmethod
    def from_smiles(cls, smiles):
        if any(c.isspace() for c in smiles) or any(c in smiles for c in (".",">","*","{","}","|")):
            raise StructureProblem("unsupported", "unsupported_representation")
        mol=parse(smiles)
        if mol is None or mol.GetNumAtoms()==0:
            raise StructureProblem("invalid", "invalid_smiles")
        if mol.GetNumHeavyAtoms()>128 or mol.GetNumAtoms()>512 or mol.GetNumBonds()>1024:
            raise StructureProblem("unsupported", "size_limit")
        if len(Chem.GetMolFrags(mol))!=1 or mol.GetStereoGroups():
            raise StructureProblem("unsupported", "unsupported_feature")
        for a in mol.GetAtoms():
            if a.HasQuery() or a.GetAtomicNum()==0 or a.GetAtomMapNum() or a.GetNumRadicalElectrons() or str(a.GetChiralTag()) not in CHIRAL:
                raise StructureProblem("unsupported", "unsupported_feature")
        for b in mol.GetBonds():
            if b.HasQuery() or str(b.GetBondType()) not in ORDERS or str(b.GetStereo()) not in STEREO:
                raise StructureProblem("unsupported", "unsupported_feature")
        # Reject supplied stereo annotations silently discarded by sanitization.
        marked=len(re.findall(r"@@?",smiles))
        if marked != sum(str(a.GetChiralTag())!="CHI_UNSPECIFIED" for a in mol.GetAtoms()):
            raise StructureProblem("unsupported", "unsupported_feature")
        if ("/" in smiles or "\\" in smiles) and not any(str(b.GetStereo())!="STEREONONE" for b in mol.GetBonds()):
            raise StructureProblem("unsupported", "unsupported_feature")
        canonical=Chem.MolToSmiles(mol,canonical=True,isomericSmiles=True)
        normalized=parse(canonical)
        if normalized is None or normalized.GetNumAtoms()!=mol.GetNumAtoms():
            raise StructureProblem("unsupported", "unsupported_feature")
        return cls(normalized,canonical)

    def graph(self):
        atoms=[Atom(index=a.GetIdx(),atomic_number=a.GetAtomicNum(),isotope=a.GetIsotope(),formal_charge=a.GetFormalCharge(),explicit_hydrogens=a.GetNumExplicitHs(),implicit_hydrogens=a.GetNumImplicitHs(),aromatic=a.GetIsAromatic(),chiral_tag=str(a.GetChiralTag())) for a in self.mol.GetAtoms()]
        bonds=[Bond(begin=b.GetBeginAtomIdx(),end=b.GetEndAtomIdx(),order=ORDERS[str(b.GetBondType())],stereo=str(b.GetStereo()),stereo_atoms=list(b.GetStereoAtoms())) for b in self.mol.GetBonds()]
        return MolecularGraph(atoms=atoms,bonds=bonds)

    def warnings(self):
        stereo=Chem.FindPotentialStereo(self.mol)
        return ["unspecified_stereochemistry"] if any(str(item.specified)=="Unspecified" for item in stereo) else []
