#!/usr/bin/env python3
"""V-N02a: independent adversarial verification of repair R-N02
(amphora-molecule-property/evidence/phase0/repairs/R-N02/done/
rn02-molecule-property-coordinated-cn-fix-repair-receipt.v1.dsse.json).

Does NOT reuse R-N02's own sweep script. Extracts n_active_amine_nh()
VERBATIM (byte-hashed, same source-marker technique as the original
refuting audit and R-N02's own sweep) from the CURRENTLY SHIPPED
compute_amine_class.py -- so this is a fresh, independent invocation
against live source, not a replay of stored bytes.

Three attack legs:
  (1) Re-run the 3 ORIGINAL refuting probes (guanidine, dicyandiamide,
      biguanide) that triggered R-N02. Refute criterion: any nonzero.
  (2) Re-run the FULL 26-record zero-regression check (3 exact anchors +
      6 monodisperse + 13 amine-class grid + 7 nonamine controls + 1
      hydroxyl probe) against the values the module's OWN benchmark data
      and receipt assert. Refute criterion: any mismatch.
  (3) Construct >=2 NOVEL amidine-family probes NOT present in R-N02's
      probe set, the 26-record regression set, or the sibling role-ranker
      DPG/DOTG probes: acetamidine, benzamidine (both true amidines with a
      C=N-bearing carbon, structurally distinct core from guanidine's
      N-C(=N)-N pattern), plus a deliberately adversarial BOUNDARY probe,
      2-aminopyridine, chosen because its exocyclic primary amine sits on
      an aromatic ring carbon that is formally single-bonded to the ring N
      in RDKit's Kekule/aromatic bond typing (GetBondTypeAsDouble()==1.5,
      not 2.0) -- i.e. it tests whether the C=N fix over-fires on aromatic
      systems that only LOOK like they contain a C=N pattern.
        - acetamidine   CH3-C(=NH)-NH2   CAS 60-10-6   expect n_active_nh=0
          (amidine carbon bears an explicit, non-aromatic C=N double bond;
          BOTH nitrogens on that carbon -- the imino =NH and the amino -NH2
          -- are excluded by the shipped rule, exactly as guanidine's three
          nitrogens are all excluded, since the rule fires per attached-
          carbon, not per specific double-bonded nitrogen.)
        - benzamidine   C6H5-C(=NH)-NH2  CAS 618-39-3  expect n_active_nh=0
          (same amidine core, aromatic substituent instead of methyl;
          checks the exclusion is substituent-independent.)
        - 2-aminopyridine  Nc1ccccn1     CAS 504-29-0  expect n_active_nh=2
          (chemically-correct truth: primary aromatic exocyclic amine,
          same class as aniline (already n_active_nh=2 in the 26-record
          set) -- the ring C-N bond is an aromatic bond, not a localized
          C=N pi-acceptor in the amidine/guanidine sense, so lone-pair
          delocalization into a SPECIFIC imine acceptor -- the shipped
          rule's own stated mechanism -- does not apply. If the shipped
          rule instead returns 0 here, that is over-exclusion: a false
          positive that would silently zero out a real, if reduced-
          nucleophilicity, primary amine hardener/accelerator component.)

Deterministic: no RNG, no wall clock, fixed hardcoded probe SMILES,
sort_keys canonical JSON. Run twice (runA/runB) for the two-replay gate.
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
R_N02_DONE = ROOT / "amphora-molecule-property/evidence/phase0/repairs/R-N02/done/rn02-molecule-property-coordinated-cn-fix-repair-receipt.v1.dsse.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ---- independent verbatim extraction of the CURRENTLY SHIPPED function
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


def run(smi):
    mol = Chem.MolFromSmiles(smi)
    n = n_active_amine_nh(mol)
    return {
        "canonical_smiles": Chem.MolToSmiles(mol),
        "formula": rdMolDescriptors.CalcMolFormula(mol),
        "mw": round(Descriptors.MolWt(mol), 4),
        "n_active_nh": n,
        "theoretical_ahew": round(Descriptors.MolWt(mol) / n, 4) if n else None,
    }


# ---------------------------------------------------------------- LEG 1: original 3 probes
ORIGINAL_PROBES = [
    ("guanidine", "NC(=N)N", "CAS 113-00-8"),
    ("dicyandiamide", "NC(=NC#N)N", "CAS 461-58-5; DICY"),
    ("biguanide", "NC(=N)NC(=N)N", "CAS 461-71-2"),
]
leg1_rows = []
leg1_all_zero = True
for name, smi, note in ORIGINAL_PROBES:
    r = run(smi)
    leg1_rows.append({"id": name, "smiles": smi, "note": note, **r})
    leg1_all_zero = leg1_all_zero and (r["n_active_nh"] == 0)

# ---------------------------------------------------------------- LEG 2: 26-record regression
# Expected n_active_nh values transcribed directly from the ALREADY-SIGNED,
# byte-verified R-N02 done receipt's own zero_regression_evidence.
# molecule_property_26_records.records table (not from any sweep script),
# so this leg checks the CURRENTLY SHIPPED function against an independent
# ground truth the receipt itself asserts and R-N02 verified byte-identical
# pre/post-fix -- it does not reuse rn02_property_sweep.py.
REGRESSION_26 = [
    ("exact-deta", "NCCNCCN", 5),
    ("exact-ipda", "CC1(C)CC(N)CC(C)(CN)C1", 4),
    ("mono-ahew-deta", "NCCNCCN", 5),
    ("mono-ahew-ipda", "CC1(C)CC(N)CC(C)(CN)C1", 4),
    ("mono-ahew-hmda", "NCCCCCCN", 4),
    ("deta", "NCCNCCN", 5),
    ("teta", "NCCNCCNCCN", 6),
    ("tepa", "NCCNCCNCCNCCN", 7),
    ("eda", "NCCN", 4),
    ("ipda", "CC1(C)CC(N)CC(C)(CN)C1", 4),
    ("hmda", "NCCCCCCN", 4),
    ("mxda", "NCc1cccc(CN)c1", 4),
    ("piperazine", "C1CNCCN1", 2),
    ("aep", "NCCN1CCNCC1", 3),
    ("dach", "NC1CCCCC1N", 4),
    ("aniline", "Nc1ccccc1", 2),
    ("mda", "Nc1ccc(Cc2ccc(N)cc2)cc1", 4),
    ("dds", "Nc1ccc(cc1)S(=O)(=O)c1ccc(N)cc1", 4),
    ("triethylamine", "CCN(CC)CC", 0),
    ("acetamide", "CC(=O)N", 0),
    ("dmf", "CN(C)C=O", 0),
    ("urea", "NC(=O)N", 0),
    ("acetonitrile", "CC#N", 0),
    ("pyridine", "c1ccncc1", 0),
    ("nitrobenzene", "O=[N+]([O-])c1ccccc1", 0),
    ("ethanolamine", "NCCO", 2),
]

leg2_rows = []
for record_id, smiles, expected_n in REGRESSION_26:
    mol = Chem.MolFromSmiles(smiles)
    got = n_active_amine_nh(mol)
    leg2_rows.append({
        "record_id": record_id, "smiles": smiles,
        "expected_n_active_nh": expected_n, "computed_n_active_nh": got,
        "match": got == expected_n,
    })

leg2_all_match = all(r["match"] for r in leg2_rows)

# ---------------------------------------------------------------- LEG 3: novel amidine-family probes
NOVEL_PROBES = [
    ("acetamidine", "CC(=N)N", 0,
     "CAS 60-10-6; simple aliphatic amidine, C=N-bearing carbon distinct "
     "from guanidine's N-C(=N)-N core; tests whether the R-N02 exclusion "
     "generalizes beyond the 3-nitrogen guanidine pattern to a 2-nitrogen "
     "amidine pattern."),
    ("benzamidine", "NC(=N)c1ccccc1", 0,
     "CAS 618-39-3; aromatic-substituted amidine; tests substituent-"
     "independence of the exclusion."),
    ("2-aminopyridine", "Nc1ccccn1", 2,
     "CAS 504-29-0; ADVERSARIAL BOUNDARY probe -- primary aromatic "
     "exocyclic amine (same class as aniline, already n_active_nh=2 in "
     "the 26-record set); the ring C-N bond is aromatic (bond order 1.5 "
     "in RDKit), not a localized C=N pi-acceptor, so the amidine/guanidine "
     "delocalization mechanism the shipped rule targets does not apply. "
     "Refutes R-N02 if the fix over-fires and zeroes this out."),
]
leg3_rows = []
leg3_all_expected = True
for name, smi, expected, note in NOVEL_PROBES:
    r = run(smi)
    match = r["n_active_nh"] == expected
    leg3_all_expected = leg3_all_expected and match
    leg3_rows.append({"id": name, "smiles": smi, "expected_n_active_nh": expected,
                       "note": note, **r, "match": match})

# ---------------------------------------------------------------- combine
all_legs_pass = leg1_all_zero and leg2_all_match and leg3_all_expected

out_obj = {
    "schema": "amphora.molecule-property.v-n02a-independent-verify-sweep.v1",
    "campaign_item_id": "V-N02a",
    "verifies_repair": "R-N02",
    "r_n02_done_receipt_sha256": sha(R_N02_DONE.read_bytes()),
    "rdkit_version_detected": Chem.rdBase.rdkitVersion,
    "target_source_file": str(TARGET.relative_to(ROOT)),
    "target_source_file_sha256": sha(TARGET.read_bytes()),
    "shipped_n_active_amine_nh_source_sha256": sha(SHIPPED_FN_SRC.encode()),
    "benchmark_data_sha256": sha(BENCH.read_bytes()),
    "target_receipt_sha256": sha(TARGET_RECEIPT.read_bytes()),
    "leg1_original_3_probes": {
        "rows": leg1_rows,
        "all_zero": leg1_all_zero,
        "refute_criterion": "any of the 3 probes returns nonzero n_active_nh",
    },
    "leg2_26_record_regression": {
        "n_records": len(leg2_rows),
        "rows": leg2_rows,
        "all_match": leg2_all_match,
        "refute_criterion": "any record's computed n_active_nh diverges from the module's own asserted truth value",
    },
    "leg3_novel_amidine_probes": {
        "rows": leg3_rows,
        "all_expected": leg3_all_expected,
        "refute_criterion": "any novel probe's computed n_active_nh diverges from its chemically-justified expected value",
    },
    "all_legs_pass": all_legs_pass,
    "verdict": "CLAIM_SURVIVED" if all_legs_pass else "CLAIM_REFUTED",
}
out = json.dumps(out_obj, indent=2, sort_keys=True)
dest = sys.argv[1]
open(dest, "w").write(out)
print("WROTE", dest, "sha256", sha(out.encode()))
print("leg1_all_zero", leg1_all_zero)
print("leg2_all_match", leg2_all_match, "n_records", len(leg2_rows))
print("leg3_all_expected", leg3_all_expected)
print("VERDICT", out_obj["verdict"])
