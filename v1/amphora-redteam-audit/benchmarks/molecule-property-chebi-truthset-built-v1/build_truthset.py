#!/usr/bin/env python3
"""Build the frozen molecule-property EEW/AHEW truth set from ChEBI-252 CC-BY,
independently cross-checked against PubChem PUG-REST (selection_lock).

Rule (deterministic given ChEBI SDF hash + PubChem snapshot):
  process full candidates in ASCENDING ChEBI-ID order; keep a candidate iff
  ChEBI-annotated, RDKit-recomputed, AND PubChem-fetched all agree:
    - identity : exact full InChIKey  (ChEBI == RDKit == PubChem)
    - formula  : exact molecular-formula string (ChEBI == RDKit == PubChem)
    - mass     : |RDKit_avg_MW - PubChem_MW| <= 0.05  AND
                 |RDKit_avg_MW - ChEBI_mass| <= 0.05
  Freeze the 300 lowest-ChEBI-ID passing molecules.
Writes truthset + pubchem response cache + KPI summary. Records PubChem snapshot."""
import json, sys, time, urllib.request, urllib.parse, hashlib

CAND = "/tmp/chebi_candidates.json"
TARGET = 300
BATCH = 100
PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/property/InChIKey,MolecularFormula,MolecularWeight/JSON"

with open(CAND) as f:
    candidates = json.load(f)

def pug_batch(cids):
    data = urllib.parse.urlencode({"cid": ",".join(cids)}).encode()
    for attempt in range(4):
        try:
            req = urllib.request.Request(PUG, data=data,
                headers={"User-Agent":"amphora-coating-truthset/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            sys.stderr.write(f"  retry {attempt} for batch: {e}\n")
            time.sleep(2.0*(attempt+1))
    raise RuntimeError("PubChem batch failed after retries")

pubchem_cache = {}   # cid -> {InChIKey, MolecularFormula, MolecularWeight}
passing = []
n_queried = 0
i = 0
while len(passing) < TARGET and i < len(candidates):
    chunk = candidates[i:i+BATCH]
    i += BATCH
    cids = [c["pubchem_cid"] for c in chunk]
    resp = pug_batch(cids)
    props = {str(p["CID"]): p for p in resp.get("PropertyTable",{}).get("Properties",[])}
    n_queried += len(chunk)
    for c in chunk:
        cid = c["pubchem_cid"]
        p = props.get(cid)
        if not p: continue
        pc_ikey = p.get("InChIKey"); pc_formula = p.get("MolecularFormula")
        pc_mw = p.get("MolecularWeight")
        if pc_ikey is None or pc_formula is None or pc_mw is None: continue
        pubchem_cache[cid] = {"InChIKey":pc_ikey,"MolecularFormula":pc_formula,"MolecularWeight":pc_mw}
        try: pc_mw_f = float(pc_mw)
        except: continue
        rd_ikey=c["rdkit_inchikey"]; rd_formula=c["rdkit_formula"]; rd_mass=c["rdkit_mass"]
        ch_ikey=c["chebi_inchikey"]; ch_formula=c["chebi_formula"]
        try: ch_mass=float(c["chebi_mass"])
        except: continue
        ident_ok  = (rd_ikey==pc_ikey==ch_ikey)
        formula_ok= (rd_formula==pc_formula==ch_formula)
        mass_ok   = (abs(rd_mass-pc_mw_f)<=0.05) and (abs(rd_mass-ch_mass)<=0.05)
        if ident_ok and formula_ok and mass_ok:
            passing.append({
                "chebi_id":c["chebi_id"],"pubchem_cid":cid,"smiles":c["smiles"],
                "canonical_smiles":c["canonical_smiles"],
                "inchikey":rd_ikey,"formula":rd_formula,
                "rdkit_avg_mw":rd_mass,"chebi_mass":ch_mass,"pubchem_mw":pc_mw_f,
            })
            if len(passing)>=TARGET: break
    sys.stderr.write(f"  queried={n_queried} passing={len(passing)}\n")
    time.sleep(0.20)

passing = passing[:TARGET]
out = {
    "schema":"amphora.molecule_property.chebi_pubchem_truthset.v1",
    "chebi_release":"ChEBI-252",
    "chebi_sdf_sha256":"8f17627476c66e899dabe3cd7ae1cbb94f7ee6c67f2ee91f077a77a19c940ad7",
    "selection_rule":"lowest-ChEBI-ID candidates passing ChEBI==RDKit==PubChem triple cross-check (InChIKey exact, formula exact, mass<=0.05 g/mol)",
    "pubchem_endpoint":PUG,
    "target_records":TARGET,
    "n_candidates_total":len(candidates),
    "n_candidates_queried":n_queried,
    "n_selected":len(passing),
    "records":passing,
}
with open("/tmp/truthset.v1.json","w") as f:
    json.dump(out,f,indent=2,sort_keys=True)
with open("/tmp/pubchem_cache.json","w") as f:
    json.dump({k:pubchem_cache[k] for k in sorted(pubchem_cache)},f,indent=2,sort_keys=True)
print(json.dumps({
    "n_candidates_total":len(candidates),"n_candidates_queried":n_queried,
    "n_pubchem_cached":len(pubchem_cache),"n_selected":len(passing),
    "pass_rate_over_queried":round(len(passing)/max(1,n_queried),4),
    "lowest_chebi":passing[0]["chebi_id"] if passing else None,
    "highest_chebi":passing[-1]["chebi_id"] if passing else None,
},indent=2))
