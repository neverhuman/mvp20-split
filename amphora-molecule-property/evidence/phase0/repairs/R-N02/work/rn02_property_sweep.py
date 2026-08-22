#!/usr/bin/env python3
"""R-N02 property-side sweep (repair_mode interactive-2026-08-03).

Runs the SHIPPED n_active_amine_nh() -- extracted VERBATIM (byte-hashed) from
amphora-molecule-property/benchmarks/amine-class-active-nh-robustness-v1/
compute_amine_class.py, same marker extraction as the refuting audit
compute_guanidine_gap.py -- over:
  (a) the 26 previously-validated regression records (3 exact anchors,
      6 monodisperse, 13 amine-grid, 7 nonamine controls, 1 hydroxyl probe;
      enumerated exactly as the refuting audit enumerated them), and
  (b) the 5 coordinated C=N probes: guanidine, dicyandiamide (DICY),
      biguanide (original refuting probes) + DPG, DOTG (sibling-module
      refuting probes, run here for cross-module rule consistency).

Deterministic: sort_keys, fixed rounding, no RNG, no wall clock.
Usage: rn02_property_sweep.py <dest.json>
Run PRE-fix and POST-fix; the diff of the two outputs is the zero-regression
and re-attack evidence embedded in the R-N02 done receipts.
"""
import hashlib
import json
import sys
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
TARGET = ROOT / "amphora-molecule-property/benchmarks/amine-class-active-nh-robustness-v1/compute_amine_class.py"
TARGET_RECEIPT = ROOT / "amphora-molecule-property/benchmarks/amine-class-active-nh-robustness-v1/amine_class_active_nh_robustness_receipt.v1.json"
BENCH = ROOT / "amphora-molecule-property/reference/mvp20/data/eew_ahew_benchmark.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---- verbatim extraction of the shipped function (same markers as the audit)
target_src = TARGET.read_text()
FN_MARK_START = "def n_active_amine_nh(mol):"
FN_MARK_END = "\n\ndef mw(mol):"
start = target_src.index(FN_MARK_START)
end = target_src.index(FN_MARK_END, start)
SHIPPED_FN_SRC = target_src[start:end]

ns = {}
exec(compile("from rdkit import Chem\n" + SHIPPED_FN_SRC,
             "<shipped_n_active_amine_nh>", "exec"), ns)
n_active_amine_nh = ns["n_active_amine_nh"]

PROBES = [
    ("guanidine", "NC(=N)N", "CAS 113-00-8; original refuting probe (a)"),
    ("dicyandiamide", "NC(=NC#N)N", "CAS 461-58-5; DICY; original refuting probe (a)"),
    ("biguanide", "NC(=N)NC(=N)N", "CAS 461-71-2; original refuting probe (a)"),
    ("dpg-diphenylguanidine-accelerator", "c1ccccc1NC(=N)Nc2ccccc2",
     "CAS 102-06-7; sibling refuting probe (b), cross-module consistency"),
    ("dotg-di-o-tolylguanidine-accelerator", "Cc1ccccc1NC(=N)Nc2ccccc2C",
     "CAS 97-39-2; sibling refuting probe (b), cross-module consistency"),
]

probe_rows = []
for name, smi, note in PROBES:
    mol = Chem.MolFromSmiles(smi)
    n = n_active_amine_nh(mol)
    probe_rows.append({
        "id": name, "smiles": smi, "note": note,
        "canonical_smiles": Chem.MolToSmiles(mol),
        "formula": rdMolDescriptors.CalcMolFormula(mol),
        "mw": round(Descriptors.MolWt(mol), 4),
        "n_active_nh": n,
        "theoretical_ahew": round(Descriptors.MolWt(mol) / n, 4) if n else None,
    })

bench = json.loads(BENCH.read_text())
target_receipt = json.loads(TARGET_RECEIPT.read_text())

regression_rows = []


def check(record_id, smiles, prop):
    if prop != "ahew":
        return
    mol = Chem.MolFromSmiles(smiles)
    regression_rows.append({
        "record_id": record_id, "smiles": smiles, "property": prop,
        "n_active_nh": n_active_amine_nh(mol),
    })


for rec in bench["exact_implementation_checks"]:
    if rec["expected"].get("ahew_g_per_eq") is not None:
        check(rec["record_id"], rec["smiles"], "ahew")

for rec in bench["independent_monodisperse_records"]:
    if rec["property"] == "ahew":
        check(rec["record_id"], rec["smiles"], "ahew")

for row in target_receipt["amine_class_grid"]:
    check(row["id"], row["smiles"], "ahew")

for row in target_receipt["nonamine_controls"]:
    check(row["id"], row["smiles"], "ahew")

hp = target_receipt["hydroxyl_exclusion_probe"]
check(hp["id"], hp["smiles"], "ahew")

out_obj = {
    "schema": "amphora.molecule-property.rn02-property-sweep.v1",
    "repair_item": "R-N02",
    "repair_mode": "interactive-2026-08-03",
    "rdkit_version_detected": Chem.rdBase.rdkitVersion,
    "target_source_file": str(TARGET.relative_to(ROOT)),
    "target_source_file_sha256": sha(TARGET.read_bytes()),
    "shipped_n_active_amine_nh_source_sha256": sha(SHIPPED_FN_SRC.encode()),
    "benchmark_data_sha256": sha(BENCH.read_bytes()),
    "target_receipt_sha256": sha(TARGET_RECEIPT.read_bytes()),
    "n_regression_records": len(regression_rows),
    "regression_records": regression_rows,
    "probe_molecules": probe_rows,
}
out = json.dumps(out_obj, indent=2, sort_keys=True)
dest = sys.argv[1]
open(dest, "w").write(out)
print("WROTE", dest, "sha256", sha(out.encode()))
print("n_regression_records", len(regression_rows))
for r in probe_rows:
    print("probe", r["id"], "n_active_nh", r["n_active_nh"])
