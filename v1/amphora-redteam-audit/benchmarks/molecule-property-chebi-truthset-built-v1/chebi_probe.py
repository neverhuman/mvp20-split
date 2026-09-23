#!/usr/bin/env python3
"""Funnel probe for molecule-property truth-set selection_lock.
Deterministic, read-only, NO network. Counts candidates that survive the
offline filters AND carry exactly one PubChem Compound CID (required for the
independent PubChem cross-check). Collects candidate CIDs for the network step."""
import gzip, json, re, sys
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit import RDLogger
RDLogger.DisableLog('rdApp.*')

SDF = "amphora-molecule-property/reference/chebi/rel252/chebi_3_stars.sdf.gz"
epoxide    = Chem.MolFromSmarts("[C;R1]1[O;R1][C;R1]1")
prim_amine = Chem.MolFromSmarts("[NX3;H2;!$(NC=O);!$(N=*)]")
sec_amine  = Chem.MolFromSmarts("[NX3;H1;!$(NC=O);!$(N=*);!$(N-a)]")

def inscope(mol):
    return mol.HasSubstructMatch(epoxide) or mol.HasSubstructMatch(prim_amine) or mol.HasSubstructMatch(sec_amine)

tot=parsed=single=defined=inscope_n=have_cid=cand=0
candidates=[]
with gzip.open(SDF,'rb') as fh:
    supplier = Chem.ForwardSDMolSupplier(fh, sanitize=True, removeHs=True)
    for mol in supplier:
        tot+=1
        if mol is None: continue
        parsed+=1
        def gp(k): return mol.GetProp(k) if mol.HasProp(k) else None
        smi_raw = gp('SMILES')
        try:
            csmi = Chem.MolToSmiles(mol)
        except Exception:
            continue
        if '.' in csmi: continue
        single+=1
        if '*' in csmi or (smi_raw and '*' in smi_raw): continue
        defined+=1
        if not inscope(mol): continue
        inscope_n+=1
        cid_field = gp('PubChem Compound Database Links')
        if not cid_field: continue
        cids = [c for c in re.split(r'[;\s]+', cid_field.strip()) if c]
        if len(cids)!=1: continue
        have_cid+=1
        chebi_id = gp('ChEBI ID'); ikey = gp('INCHIKEY'); formula = gp('FORMULA'); mass = gp('MASS')
        if not all([chebi_id, smi_raw, ikey, formula, mass]): continue
        cand+=1
        candidates.append({
            "chebi_id": chebi_id, "chebi_num": int(chebi_id.split(':')[1]),
            "smiles": smi_raw, "canonical_smiles": csmi,
            "chebi_inchikey": ikey, "chebi_formula": formula, "chebi_mass": mass,
            "pubchem_cid": cids[0],
            "rdkit_inchikey": Chem.MolToInchiKey(mol),
            "rdkit_formula": rdMolDescriptors.CalcMolFormula(mol),
            "rdkit_mass": round(Descriptors.MolWt(mol),4),
        })
print(json.dumps({
    "total_records": tot, "rdkit_parsed": parsed, "single_component": single,
    "defined_no_wildcard": defined, "in_scope": inscope_n,
    "in_scope_single_pubchem_cid": have_cid, "full_candidates": cand,
}, indent=2))
candidates.sort(key=lambda r: r["chebi_num"])
with open("/tmp/chebi_candidates.json","w") as f:
    json.dump(candidates, f)
print("candidates_written", len(candidates), file=sys.stderr)
