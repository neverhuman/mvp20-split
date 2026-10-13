"""Formula and inert bounded depiction derived from the same normalized molecule."""
import base64
import hashlib
from dataclasses import dataclass
from rdkit import rdBase
from rdkit.Chem import rdMolDescriptors, rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
from amphora_contracts_chemical_structure import Formula, Depiction, DerivationMethod, DerivedStructure
from .profile import StructureProblem

@dataclass(frozen=True)
class DisplayBundle:
    molecule: object
    profile: object

    def formula(self):
        return Formula(text=rdMolDescriptors.CalcMolFormula(self.molecule.mol,separateIsotopes=True,abbreviateHIsotopes=False),isotope_policy="separate_isotopes",charge_policy="explicit_net_formal_charge",net_formal_charge=sum(a.GetFormalCharge() for a in self.molecule.mol.GetAtoms()))

    def depiction(self):
        rdDepictor.Compute2DCoords(self.molecule.mol,canonOrient=True,clearConfs=True,forceRDKit=True)
        drawer=rdMolDraw2D.MolDraw2DCairo(800,600)
        drawer.drawOptions().includeMetadata=False
        rdMolDraw2D.PrepareAndDrawMolecule(drawer,self.molecule.mol)
        drawer.FinishDrawing()
        raw=drawer.GetDrawingText()
        if len(raw)>131072 or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise StructureProblem("error", "size_limit")
        return Depiction(media_type="image/png",width=800,height=600,sha256=hashlib.sha256(raw).hexdigest(),png_base64=base64.b64encode(raw).decode("ascii"))

    def to_wire(self):
        return DerivedStructure(status="derived",authority="structural_derivation",method=DerivationMethod(toolkit="rdkit",toolkit_version=rdBase.rdkitVersion,method="finite-smiles-2d-v1",environment_sha256=self.profile.environment_sha256),canonical_isomeric_smiles=self.molecule.canonical,graph=self.molecule.graph(),formula=self.formula(),depiction=self.depiction(),warnings=self.molecule.warnings())
