#!/usr/bin/env python3
"""Deterministic OFFLINE verifier for the ChEBI-252/PubChem coating truth set.
No network. Reads frozen truthset + recorded PubChem cache, recomputes RDKit
facts, re-checks the independent triple cross-check, computes EEW/AHEW domain
coverage, and re-validates the 3 independent EXACT accuracy anchors. Emits a
canonical diagnostic; running twice must be byte-identical (two-replay gate)."""
import json, hashlib, sys
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit import RDLogger
RDLogger.DisableLog('rdApp.*')

BASE = "amphora-redteam-audit/benchmarks/molecule-property-chebi-truthset-built-v1"
TRUTH = json.load(open(f"{BASE}/coating_truthset_300.v1.json"))
CACHE = json.load(open(f"{BASE}/pubchem_cross_check_cache.v1.json"))

oxirane = Chem.MolFromSmarts("[C;R1]1[O;R1][C;R1]1")
prim = Chem.MolFromSmarts("[NX3;H2;!$(NC=O);!$(N=*)]")
sec  = Chem.MolFromSmarts("[NX3;H1;!$(NC=O);!$(N=*);!$(N-a)]")

def facts(smiles):
    m = Chem.MolFromSmiles(smiles)
    if m is None: return None
    n_ox = len(m.GetSubstructMatches(oxirane))
    n_nh = 2*len(m.GetSubstructMatches(prim)) + 1*len(m.GetSubstructMatches(sec))
    return {
        "inchikey": Chem.MolToInchiKey(m),
        "formula": rdMolDescriptors.CalcMolFormula(m),
        "avg_mw": round(Descriptors.MolWt(m), 4),
        "oxirane": n_ox, "active_nh": n_nh,
    }

# ---- 1. re-verify the 300-molecule independent triple cross-check (offline) ----
triple_ok = 0
max_dm_pc = 0.0   # rdkit vs pubchem
max_dm_ch = 0.0   # rdkit vs chebi
cov_eew = cov_ahew = 0
per = []
for r in TRUTH["records"]:
    f = facts(r["canonical_smiles"])
    assert f is not None, r["chebi_id"]
    pc = CACHE[r["pubchem_cid"]]
    pc_mw = float(pc["MolecularWeight"])
    ident = (f["inchikey"] == pc["InChIKey"] == r["inchikey"])
    formu = (f["formula"] == pc["MolecularFormula"] == r["formula"])
    dpc = abs(f["avg_mw"] - pc_mw); dch = abs(f["avg_mw"] - r["chebi_mass"])
    massok = (dpc <= 0.05 and dch <= 0.05)
    if ident and formu and massok: triple_ok += 1
    max_dm_pc = max(max_dm_pc, dpc); max_dm_ch = max(max_dm_ch, dch)
    eew = round(f["avg_mw"]/f["oxirane"], 3) if f["oxirane"] else None
    ahew = round(f["avg_mw"]/f["active_nh"], 3) if f["active_nh"] else None
    if eew is not None: cov_eew += 1
    if ahew is not None: cov_ahew += 1

# ---- 2. re-validate independent EXACT accuracy anchors (defined coating molecules) ----
anchors = [
    {"id":"DGEBA","smiles":"C(C1=CC=C(OCC2CO2)C=C1)(C)(C)C1=CC=C(OCC2CO2)C=C1","prop":"eew","ref":170.2,"src":"PubChem 340.42 / ASTM D1652"},
    {"id":"DETA","smiles":"NCCNCCN","prop":"ahew","ref":20.6,"src":"titration amine value"},
    {"id":"IPDA","smiles":"CC1(C)CC(N)CC(C)(CN)C1","prop":"ahew","ref":42.6,"src":"supplier MW 170.30"},
]
anchor_max_err = 0.0
anchor_rows = []
for a in anchors:
    f = facts(a["smiles"])
    val = round(f["avg_mw"]/f["oxirane"],3) if a["prop"]=="eew" else round(f["avg_mw"]/f["active_nh"],3)
    err = round(abs(val - a["ref"]), 4)
    anchor_max_err = max(anchor_max_err, err)
    anchor_rows.append({"id":a["id"],"property":a["prop"],"computed":val,"reference":a["ref"],
                        "abs_error_g_per_eq":err,"reference_source":a["src"]})

diag = {
    "schema": "amphora.molecule_property.chebi_pubchem_truthset_diagnostic.v1",
    "authority": "AUDIT_ONLY",
    "rdkit_version": Chem.rdBase.rdkitVersion,
    "chebi_release": TRUTH["chebi_release"],
    "chebi_sdf_sha256": TRUTH["chebi_sdf_sha256"],
    "selection_rule": TRUTH["selection_rule"],
    "funnel": {
        "candidates_total_in_scope_single_cid": TRUTH["n_candidates_total"],
        "candidates_queried_ascending": TRUTH["n_candidates_queried"],
        "selected": TRUTH["n_selected"],
    },
    "independent_cross_check": {
        "n_truth_set": len(TRUTH["records"]),
        "triple_agreement_pass": triple_ok,
        "triple_agreement_rate": round(triple_ok/len(TRUTH["records"]), 6),
        "max_mass_abs_err_rdkit_vs_pubchem_g_per_mol": round(max_dm_pc, 4),
        "max_mass_abs_err_rdkit_vs_chebi_g_per_mol": round(max_dm_ch, 4),
        "identity_rule": "exact full InChIKey (ChEBI==RDKit==PubChem)",
        "formula_rule": "exact molecular formula string (ChEBI==RDKit==PubChem)",
        "mass_rule": "abs diff <= 0.05 g/mol vs both PubChem and ChEBI",
    },
    "domain_coverage": {
        "eew_computable_epoxide": cov_eew,
        "ahew_computable_amine": cov_ahew,
        "reactive_group_computable_total": cov_eew + cov_ahew,
        "coverage_rate": round((cov_eew + cov_ahew)/len(TRUTH["records"]), 6),
    },
    "exact_accuracy_anchors": {
        "rows": anchor_rows,
        "max_abs_error_g_per_eq": anchor_max_err,
        "bar_g_per_eq": 0.5,
        "pass": anchor_max_err <= 0.5,
    },
    "gates": {
        "minimum_300_truth_set_molecules": len(TRUTH["records"]) >= 300,
        "independent_triple_agreement_100pct": triple_ok == len(TRUTH["records"]),
        "exact_anchor_error_at_most_0_5": anchor_max_err <= 0.5,
    },
}
out = json.dumps(diag, indent=2, sort_keys=True)
sys.stdout.write(out + "\n")
