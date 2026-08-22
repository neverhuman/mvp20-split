#!/usr/bin/env python3
"""Count in-scope reactive (epoxide / amine N-H) molecules in ChEBI 3-star SDF.
Read-only feasibility probe for the molecule-property EEW/AHEW >=300 truth-set gate.
No files written. Deterministic."""
import gzip, sys
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit import RDLogger
RDLogger.DisableLog('rdApp.*')

SDF = "amphora-molecule-property/reference/chebi/rel252/chebi_3_stars.sdf.gz"

# Substructure definitions (SMARTS)
epoxide = Chem.MolFromSmarts("[C;R1]1[O;R1][C;R1]1")          # oxirane ring
prim_amine = Chem.MolFromSmarts("[NX3;H2;!$(NC=O);!$(N=*)]")   # primary aliphatic amine N-H2
sec_amine  = Chem.MolFromSmarts("[NX3;H1;!$(NC=O);!$(N=*);!$(N-a)]")  # secondary amine N-H (non-amide, non-aniline-only)

tot=0; parsed=0; single=0; defined=0
n_epoxide=0; n_amine=0; n_inscope=0; n_multi_epoxide=0
examples=[]
with gzip.open(SDF,'rt',errors='replace') as fh:
    supplier = Chem.ForwardSDMolSupplier(fh, sanitize=True, removeHs=True)
    for mol in supplier:
        tot+=1
        if mol is None:
            continue
        parsed+=1
        smi = Chem.MolToSmiles(mol)
        if '.' in smi:          # multiple components
            continue
        single+=1
        if '*' in smi:          # wildcard/polymer
            continue
        defined+=1
        has_ep = mol.HasSubstructMatch(epoxide)
        has_am = mol.HasSubstructMatch(prim_amine) or mol.HasSubstructMatch(sec_amine)
        if has_ep:
            n_epoxide+=1
            if len(mol.GetSubstructMatches(epoxide))>=2: n_multi_epoxide+=1
        if has_am: n_amine+=1
        if has_ep or has_am:
            n_inscope+=1
            if len(examples)<12:
                nm = mol.GetProp('ChEBI Name') if mol.HasProp('ChEBI Name') else (mol.GetProp('_Name') if mol.HasProp('_Name') else '?')
                cls = ('epoxide' if has_ep else '')+('+amine' if has_am else '')
                examples.append((nm[:40], cls, round(Descriptors.MolWt(mol),1)))

print(f"total_records            {tot}")
print(f"rdkit_parsed            {parsed}")
print(f"single_component        {single}")
print(f"defined_no_wildcard     {defined}")
print(f"with_epoxide            {n_epoxide}  (>=2 epoxide: {n_multi_epoxide})")
print(f"with_amine_NH           {n_amine}")
print(f"IN_SCOPE_epoxide_or_amine {n_inscope}")
print(f">=300 gate reachable:   {n_inscope>=300}")
print("examples:")
for e in examples: print("   ", e)
